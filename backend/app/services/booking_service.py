from typing import Protocol
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Booking, BookingGroupMetadata, SlotPolicy
from app.schemas.core import BookingCreate
from app.schemas.farmer_api import BookingDetail, CancelRequest
from app.services.auth_service import Principal, validate_actor
from app.core.errors import CapacityConflict, Conflict, InvalidRequest, NotFound
from app.db.base import utc_now
from app.db.transactions import serialized_write
from app.models.enums import BookingStatus
from app.services.centre_service import TERMINAL, get_centre, get_commodity, slot_snapshot, validate_visit


class BookingService(Protocol):
    """Implement owner checks and atomic capacity allocation before exposing APIs."""
    def create(self, actor: Principal, draft: BookingCreate) -> Booking: ...
    def cancel(self, actor: Principal, booking_id: str, expected_version: int) -> Booking: ...


def create_booking(db: Session, actor: Principal, draft: BookingCreate) -> BookingDetail:
    with serialized_write(db):
        validate_actor(db, actor, farmer=True)
        validate_visit(draft.appointment_date, draft.quantity)
        centre, commodity = get_centre(db, draft.centre_id), get_commodity(db, draft.commodity_id)
        if commodity not in centre.commodities:
            raise InvalidRequest()
        policy = db.scalar(select(SlotPolicy).where(SlotPolicy.centre_id == centre.id, SlotPolicy.start_time == draft.start_time))
        if policy is None or draft.start_time.tzinfo is not None:
            raise InvalidRequest()
        if not slot_snapshot(db, centre, commodity, policy, draft.appointment_date, draft.quantity).available:
            raise CapacityConflict()
        booking = Booking(farmer_id=actor.user_id, centre=centre, commodity=commodity,
            quantity=draft.quantity, appointment_date=draft.appointment_date, start_time=draft.start_time,
            token="PF-" + uuid4().hex.upper())
        if draft.group_metadata is not None:
            booking.group_metadata = BookingGroupMetadata(**draft.group_metadata.model_dump())
        db.add(booking)
        db.flush()
        result = BookingDetail.model_validate(booking)
    return result


def owned_booking(db: Session, actor: Principal, booking_id: str) -> Booking:
    validate_actor(db, actor, farmer=True)
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.farmer_id == actor.user_id))
    if booking is None:
        raise NotFound()  # Do not reveal another owner's booking existence.
    return booking


def list_bookings(db: Session, actor: Principal, active: bool | None, history: bool | None,
                  status: BookingStatus | None, group: bool | None):
    validate_actor(db, actor, farmer=True)
    if active is not None and history is not None and active == history:
        raise InvalidRequest()
    query = select(Booking).where(Booking.farmer_id == actor.user_id)
    terminal = history if history is not None else (not active if active is not None else None)
    if terminal is not None:
        query = query.where(Booking.status.in_(TERMINAL) if terminal else Booking.status.not_in(TERMINAL))
    if status is not None:
        query = query.where(Booking.status == status)
    if group is not None:
        query = query.where(Booking.group_metadata.has() if group else ~Booking.group_metadata.has())
    return [BookingDetail.model_validate(b) for b in db.scalars(query.order_by(Booking.created_at.desc(), Booking.id))]


def cancel_booking(db: Session, actor: Principal, booking_id: str, payload: CancelRequest):
    with serialized_write(db):
        booking = owned_booking(db, actor, booking_id)
        # Preserve the existing UI rule: cancellation is only allowed before check-in.
        if booking.version != payload.expected_version or booking.status != BookingStatus.BOOKED:
            raise Conflict()
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = utc_now()
        booking.cancellation_reason = payload.reason
        db.flush()
        result = BookingDetail.model_validate(booking)
    return result
