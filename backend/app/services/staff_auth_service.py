from datetime import timedelta
from functools import lru_cache
import hashlib
import hmac
import secrets
from uuid import uuid4
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import RateLimited, Unauthorized
from app.core.security import hash_password, verify_password
from app.db.base import utc_now
from app.db.transactions import serialized_write
from app.models import AuthSession, StaffAuthAttempt, StaffProfile, User
from app.schemas.farmer_api import ChallengeRead, SessionRead, StaffLogin
from app.services.auth_service import DatabaseSessionService, identity, otp_digest, prototype_secret, token_digest
from app.services.authorization import OPERATORS


@lru_cache(maxsize=1)
def dummy_hash():
    return hash_password(secrets.token_urlsafe(32))


def eligible(user: User | None) -> bool:
    return bool(user and user.is_active and user.staff_profile and user.password_hash
                and {role.name for role in user.roles}.intersection(OPERATORS))


def credential_digest(user: User) -> str:
    return hashlib.sha256(user.password_hash.encode()).hexdigest()


def staff_login(db: Session, payload: StaffLogin) -> ChallengeRead:
    key = prototype_secret()
    digest = hmac.new(key, payload.identifier.encode(), hashlib.sha256).hexdigest()
    result = None
    with serialized_write(db):
        now = utc_now()
        recent = list(db.scalars(select(StaffAuthAttempt).where(
            StaffAuthAttempt.identifier_digest == digest, StaffAuthAttempt.created_at > now - timedelta(hours=1))
            .order_by(StaffAuthAttempt.created_at.desc())))
        if len(recent) >= 5:
            raise RateLimited(max(1, 3600 - int((now - recent[-1].created_at).total_seconds())))
        successful = next((r for r in recent if r.otp_digest is not None), None)
        if successful and (now - successful.created_at).total_seconds() < 60:
            raise RateLimited(max(1, 60 - int((now - successful.created_at).total_seconds())))
        if db.scalar(select(func.count()).select_from(StaffAuthAttempt).where(StaffAuthAttempt.created_at > now - timedelta(hours=1))) >= 1000:
            raise RateLimited(3600)
        # One canonical identifier: StaffProfile.employee_code, not ambiguous user inputs.
        user = db.scalar(select(User).join(StaffProfile).where(StaffProfile.employee_code == payload.identifier))
        password_ok = verify_password(payload.password.get_secret_value(), user.password_hash if eligible(user) else dummy_hash())
        attempt = StaffAuthAttempt(id=str(uuid4()), identifier_digest=digest, environment=settings.APP_ENV,
            created_at=now, expires_at=now + timedelta(seconds=settings.OTP_TTL_SECONDS))
        db.add(attempt)
        if password_ok and eligible(user):
            for previous in recent:
                if previous.consumed_at is None:
                    previous.consumed_at = now
            otp = f"{secrets.randbelow(1000000):06d}"
            attempt.user_id = user.id
            attempt.credential_digest = credential_digest(user)
            attempt.otp_digest = otp_digest(attempt.id, otp)
            result = ChallengeRead(challenge_id=attempt.id, expires_at=attempt.expires_at,
                retry_after_seconds=60, development_otp=otp)
    if result is None:
        raise Unauthorized()  # Persist the failed password attempt without logging credentials.
    return result


def verify_staff_otp(db: Session, challenge_id: str, otp: str) -> SessionRead:
    prototype_secret()
    result = None
    with serialized_write(db):
        challenge = db.get(StaffAuthAttempt, challenge_id)
        if (challenge is None or challenge.otp_digest is None or challenge.environment != settings.APP_ENV
                or challenge.consumed_at is not None or challenge.expires_at <= utc_now() or challenge.attempts >= 5):
            raise Unauthorized()
        challenge.attempts += 1
        user = db.get(User, challenge.user_id)
        if (hmac.compare_digest(challenge.otp_digest, otp_digest(challenge.id, otp))
                and eligible(user) and hmac.compare_digest(challenge.credential_digest, credential_digest(user))):
            challenge.consumed_at = utc_now()
            token = DatabaseSessionService(db).issue(user.id, "staff_otp")
            session = db.scalar(select(AuthSession).where(AuthSession.token_digest == token_digest(token)))
            result = SessionRead(**identity(user, staff=True).model_dump(), access_token=token, expires_at=session.expires_at)
    if result is None:
        raise Unauthorized()
    return result
