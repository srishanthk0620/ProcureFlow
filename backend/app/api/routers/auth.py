from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.api.dependencies import get_bearer_token, get_current_principal
from app.db.session import get_db
from app.schemas.farmer_api import ChallengeRead, IdentityRead, MobileRequest, OtpVerify, SessionRead
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
    return identity(validate_actor(db, actor))


@router.post("/logout", status_code=204, dependencies=[Depends(no_store)])
def logout(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)):
    DatabaseSessionService(db).revoke(token)
