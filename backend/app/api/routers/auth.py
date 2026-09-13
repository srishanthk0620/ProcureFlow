from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.dependencies import get_bearer_token, get_current_principal
from app.db.session import get_db
from app.schemas.farmer_api import ChallengeRead, IdentityRead, MobileRequest, OtpVerify, SessionRead
from app.schemas.farmer_api import StaffLogin
from app.services.staff_auth_service import staff_login, verify_staff_otp
from app.services.authorization import OPERATORS
from app.services.auth_service import (DatabaseSessionService, Principal, identity,
    request_otp, validate_actor, verify_otp)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def no_store(response: Response):
    response.headers["Cache-Control"] = "no-store"


@router.post("/farmer/otp/request", response_model=ChallengeRead, response_model_exclude_none=True, dependencies=[Depends(no_store)])
def request(payload: MobileRequest, db: Session = Depends(get_db)):
    return request_otp(db, payload.mobile)


@router.post("/farmer/otp/verify", response_model=SessionRead, dependencies=[Depends(no_store)])
def verify(payload: OtpVerify, db: Session = Depends(get_db)):
    return verify_otp(db, payload.challenge_id, payload.otp)


@router.get("/me", response_model=IdentityRead, dependencies=[Depends(no_store)])
def me(actor: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return identity(validate_actor(db, actor), staff=bool(actor.roles.intersection(OPERATORS)))


@router.post("/logout", status_code=204, dependencies=[Depends(no_store)])
def logout(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)):
    DatabaseSessionService(db).revoke(token)


@router.post("/staff/login", response_model=ChallengeRead, response_model_exclude_none=True, dependencies=[Depends(no_store)])
def login_staff(payload: StaffLogin, db: Session = Depends(get_db)):
    return staff_login(db, payload)


@router.post("/staff/otp/verify", response_model=SessionRead, dependencies=[Depends(no_store)])
def verify_staff(payload: OtpVerify, db: Session = Depends(get_db)):
    return verify_staff_otp(db, payload.challenge_id, payload.otp)
