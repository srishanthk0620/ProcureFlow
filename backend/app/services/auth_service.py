from dataclasses import dataclass
from typing import Protocol
from datetime import timedelta
import hashlib
import hmac
import secrets
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import AuthUnavailable, Forbidden, RateLimited, Unauthorized
from app.db.base import utc_now
from app.db.transactions import serialized_write
from app.models import AuthSession, FarmerProfile, OtpChallenge, Role, User
from app.schemas.farmer_api import ChallengeRead, FarmerProfileRead, IdentityRead, SessionRead, StaffProfileRead
from app.schemas.core import UserRead

from app.models.enums import RoleName


@dataclass(frozen=True)
class Principal:
    user_id: str
    roles: frozenset[RoleName]
    centre_ids: frozenset[str] = frozenset()
    session_id: str | None = None


class SessionService(Protocol):
    """Server-verified identity, expiry and revocation boundary.

    Client role/user headers must never construct a trusted Principal.
    """
    def issue(self, user_id: str) -> str: ...
    def resolve(self, token: str) -> Principal: ...
    def revoke(self, token: str) -> None: ...


def prototype_secret() -> bytes:
    secret = settings.AUTH_OTP_SECRET
    if settings.APP_ENV not in {"development", "test"} or secret is None or len(secret.get_secret_value()) < 32:
        raise AuthUnavailable()
    return secret.get_secret_value().encode()


def otp_digest(challenge_id: str, otp: str) -> str:
    return hmac.new(prototype_secret(), (challenge_id + ":" + otp).encode(), hashlib.sha256).hexdigest()


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def identity(user: User, staff: bool = False) -> IdentityRead:
    allowed = {RoleName.STAFF, RoleName.CENTRE_MANAGER} if staff else {RoleName.FARMER}
    public_user = UserRead.model_validate(user)
    public_user.roles = [role for role in public_user.roles if role.name in allowed]
    return IdentityRead(user=public_user, farmer_profile=(
        FarmerProfileRead.model_validate(user.farmer_profile) if user.farmer_profile else None),
        staff_profile=StaffProfileRead.model_validate(user.staff_profile) if staff and user.staff_profile else None,
        permitted_centre_ids=[user.staff_profile.centre_id] if staff and user.staff_profile else [])


def principal_for(db: Session, session: AuthSession | None) -> Principal:
    if session is None or session.revoked_at is not None or session.expires_at <= utc_now() or session.environment != settings.APP_ENV:
        raise Unauthorized()
    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise Unauthorized()
    permitted = {RoleName.STAFF, RoleName.CENTRE_MANAGER} if session.auth_method == "staff_otp" else {RoleName.FARMER}
    roles = frozenset(role.name for role in user.roles if role.name in permitted)
    if not roles or session.auth_method == "staff_otp" and user.staff_profile is None:
        raise Unauthorized()
    return Principal(user.id, roles,
        frozenset({user.staff_profile.centre_id}) if session.auth_method == "staff_otp" and user.staff_profile else frozenset(), session.id)


def validate_actor(db: Session, actor: Principal, farmer: bool = False) -> User:
    current = principal_for(db, db.get(AuthSession, actor.session_id)) if actor.session_id else None
    if current is None or current.user_id != actor.user_id:
        raise Unauthorized()
    user = db.get(User, current.user_id)
    if farmer and (RoleName.FARMER not in current.roles or user.farmer_profile is None):
        raise Forbidden()
    return user


class DatabaseSessionService:
    def __init__(self, db: Session):
        self.db = db

    def issue(self, user_id: str, auth_method: str = "farmer_otp") -> str:
        # Called only inside the verified challenge transaction.
        token = secrets.token_urlsafe(32)
        self.db.add(AuthSession(user_id=user_id, token_digest=token_digest(token),
            environment=settings.APP_ENV, auth_method=auth_method,
            expires_at=utc_now() + timedelta(seconds=settings.SESSION_TTL_SECONDS)))
        self.db.flush()
        return token

    def resolve(self, token: str) -> Principal:
        if not 32 <= len(token) <= 128:
            raise Unauthorized()
        return principal_for(self.db, self.db.scalar(select(AuthSession).where(AuthSession.token_digest == token_digest(token))))

    def revoke(self, token: str) -> None:
        with serialized_write(self.db):
            actor = self.resolve(token)
            self.db.get(AuthSession, actor.session_id).revoked_at = utc_now()


def request_otp(db: Session, mobile: str) -> ChallengeRead:
    prototype_secret()  # Production never creates or exposes development challenges.
    with serialized_write(db):
        now = utc_now()
        recent = list(db.scalars(select(OtpChallenge).where(OtpChallenge.mobile == mobile,
            OtpChallenge.created_at > now - timedelta(hours=1)).order_by(OtpChallenge.created_at.desc())))
        if recent and (now - recent[0].created_at).total_seconds() < 60:
            raise RateLimited(max(1, 60 - int((now - recent[0].created_at).total_seconds())))
        if len(recent) >= 5:
            raise RateLimited(max(1, 3600 - int((now - recent[-1].created_at).total_seconds())))
        if db.scalar(select(func.count()).select_from(OtpChallenge).where(OtpChallenge.created_at > now - timedelta(hours=1))) >= 1000:
            raise RateLimited(3600)
        for old in recent:
            if old.consumed_at is None:
                old.consumed_at = now
        challenge_id, otp = str(uuid4()), f"{secrets.randbelow(1000000):06d}"
        expiry = now + timedelta(seconds=settings.OTP_TTL_SECONDS)
        db.add(OtpChallenge(id=challenge_id, mobile=mobile, otp_digest=otp_digest(challenge_id, otp),
            environment=settings.APP_ENV, created_at=now, expires_at=expiry))
        result = ChallengeRead(challenge_id=challenge_id, expires_at=expiry, retry_after_seconds=60, development_otp=otp)
    return result


def verify_otp(db: Session, challenge_id: str, otp: str) -> SessionRead:
    prototype_secret()
    invalid = False
    result = None
    with serialized_write(db):
        challenge = db.get(OtpChallenge, challenge_id)
        if challenge is None or challenge.environment != settings.APP_ENV or challenge.consumed_at is not None or challenge.expires_at <= utc_now() or challenge.attempts >= 5:
            raise Unauthorized()
        challenge.attempts += 1
        if not hmac.compare_digest(challenge.otp_digest, otp_digest(challenge.id, otp)):
            invalid = True  # Persist failed attempt before raising the public error.
        else:
            user = db.scalar(select(User).where(User.mobile == challenge.mobile))
            if user is None:
                role = db.scalar(select(Role).where(Role.name == RoleName.FARMER))
                if role is None:
                    role = Role(name=RoleName.FARMER)
                    db.add(role)
                user = User(display_name="Development Farmer", mobile=challenge.mobile, is_active=True, roles=[role])
                user.farmer_profile = FarmerProfile(district="Kollam", state="Kerala")
                db.add(user)
                db.flush()
            if not user.is_active or user.farmer_profile is None or RoleName.FARMER not in {r.name for r in user.roles}:
                raise Forbidden()
            challenge.consumed_at = utc_now()
            token = DatabaseSessionService(db).issue(user.id)
            session = db.scalar(select(AuthSession).where(AuthSession.token_digest == token_digest(token)))
            result = SessionRead(**identity(user).model_dump(), access_token=token, expires_at=session.expires_at)
    if invalid:
        raise Unauthorized()
    return result
