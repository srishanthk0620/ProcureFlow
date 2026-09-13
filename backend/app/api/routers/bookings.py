from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.enums import BookingStatus, RoleName
from app.schemas.core import BookingCreate
from app.schemas.farmer_api import BookingDetail, CancelRequest
from app.services.auth_service import Principal
from app.services.booking_service import booking_detail, cancel_booking, create_booking, list_bookings, owned_booking

router = APIRouter(prefix="/api/bookings", tags=["bookings"])
farmer = require_roles(RoleName.FARMER)


@router.post("", response_model=BookingDetail, status_code=201)
def create(payload: BookingCreate, actor: Principal = Depends(farmer), db: Session = Depends(get_db)):
    return create_booking(db, actor, payload)


@router.get("", response_model=list[BookingDetail])
def listing(active: bool | None = None, history: bool | None = None, status: BookingStatus | None = None,
            group: bool | None = None, actor: Principal = Depends(farmer), db: Session = Depends(get_db)):
    return list_bookings(db, actor, active, history, status, group)


@router.get("/{booking_id}", response_model=BookingDetail)
def detail(booking_id: str, actor: Principal = Depends(farmer), db: Session = Depends(get_db)):
    return booking_detail(db, owned_booking(db, actor, booking_id))


@router.post("/{booking_id}/cancel", response_model=BookingDetail)
def cancel(booking_id: str, payload: CancelRequest, actor: Principal = Depends(farmer), db: Session = Depends(get_db)):
    return cancel_booking(db, actor, booking_id, payload)
