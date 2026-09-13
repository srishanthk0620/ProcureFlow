from typing import Literal, Protocol
from app.models import QueueEntry
from app.services.auth_service import Principal
from datetime import date
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from app.core.errors import Conflict, Forbidden, NotFound
from app.db.base import utc_now
from app.db.transactions import serialized_write
from app.models import Booking, Disruption
from app.models.enums import BookingStatus, NoticeType, OperatingStatus, QueueStage
from app.schemas.core import CommodityRead
from app.schemas.farmer_api import CentreSummary
from app.schemas.operations import FarmerSummary, QueueActionInput, QueueStatus, VersionAction
from app.services.auth_service import validate_actor
from app.services.authorization import centre_access, OPERATORS
from app.services.centre_service import local_today
from app.services.eta_service import booking_eta
from app.services.notification_service import notify_booking

QueueAction = Literal["check_in", "advance", "hold", "resume", "complete"]


class QueueService(Protocol):
    """Future centre-scoped transitions; update booking, queue and notices atomically."""
    def transition(self, actor: Principal, entry_id: str, action: QueueAction,
                   expected_version: int) -> QueueEntry: ...


def begin_snapshot(db: Session):
    # SQLite's legacy driver does not BEGIN for SELECT automatically.
    if not db.in_transaction() and db.get_bind().dialect.name == "sqlite":
        db.execute(text("BEGIN"))


def status_snapshot(db: Session, booking: Booking) -> QueueStatus:
    entry = booking.queue_entry
    eta, position, ahead = booking_eta(db, booking)
    timestamps = [booking.updated_at]
    if entry:
        timestamps.append(entry.updated_at)
    for model, column in [(QueueEntry, QueueEntry.updated_at), (Disruption, Disruption.created_at), (Disruption, Disruption.resolved_at)]:
        updated = db.scalar(select(func.max(column)).where(model.centre_id == booking.centre_id))
        if updated:
            timestamps.append(updated)
    return QueueStatus(booking_id=booking.id, token=booking.token,
        centre=CentreSummary.model_validate(booking.centre), farmer=FarmerSummary(display_name=booking.farmer.user.display_name),
        commodity=CommodityRead.model_validate(booking.commodity), quantity=booking.quantity,
        appointment_date=booking.appointment_date, start_time=booking.start_time,
        queue_id=entry.id if entry else None, checked_in=bool(entry and entry.checked_in_at),
        current_stage=booking.status, held=bool(entry and entry.held), position=position, bookings_ahead=ahead,
        checked_in_at=entry.checked_in_at if entry else None,
        quality_started_at=entry.quality_started_at if entry else None,
        weighing_started_at=entry.weighing_started_at if entry else None,
        completed_at=entry.completed_at if entry else None,
        version=entry.version if entry else booking.version, booking_version=booking.version,
        updated_at=max(timestamps), server_time=eta.calculated_at, eta=eta)


def get_status(db: Session, actor: Principal, booking_id: str):
    begin_snapshot(db)
    validate_actor(db, actor)
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise NotFound()
    if actor.roles.intersection(OPERATORS):
        centre_access(db, actor, booking.centre_id)
    elif booking.farmer_id != actor.user_id:
        raise NotFound()
    return status_snapshot(db, booking)


def list_queue(db: Session, actor: Principal, centre_id: str | None, appointment_date: date | None,
               stage: QueueStage | None, held: bool | None, commodity: str | None, limit: int, offset: int):
    begin_snapshot(db)
    assigned = centre_access(db, actor, centre_id)
    query = select(Booking).join(QueueEntry, QueueEntry.booking_id == Booking.id).where(Booking.centre_id == assigned)
    if appointment_date is not None:
        query = query.where(Booking.appointment_date == appointment_date)
    if stage is not None:
        query = query.where(QueueEntry.current_stage == stage)
    else:
        query = query.where(Booking.status.not_in([BookingStatus.COMPLETED, BookingStatus.CANCELLED]))
    if held is not None:
        query = query.where(QueueEntry.held.is_(held))
    if commodity is not None:
        from app.models import Commodity
        query = query.where(Booking.commodity.has((Commodity.id == commodity) | (Commodity.code == commodity)))
    bookings = db.scalars(query.order_by(QueueEntry.held, QueueEntry.checked_in_at,
        Booking.appointment_date, Booking.start_time, QueueEntry.id).offset(offset).limit(limit))
    return [status_snapshot(db, b) for b in bookings]


def check_in(db: Session, actor: Principal, booking_id: str, payload: VersionAction):
    with serialized_write(db):
        booking = db.get(Booking, booking_id)
        if booking is None:
            raise NotFound()
        centre_access(db, actor, booking.centre_id)
        if (booking.version != payload.expected_version or booking.status != BookingStatus.BOOKED
                or booking.queue_entry is not None or booking.appointment_date != local_today()
                or not booking.centre.is_active or booking.centre.operating_status != OperatingStatus.OPEN):
            raise Conflict()
        booking.status = BookingStatus.CHECKED_IN
        booking.queue_entry = QueueEntry(centre_id=booking.centre_id, current_stage=QueueStage.CHECKED_IN,
            checked_in_at=utc_now())
        notify_booking(db, booking, NoticeType.QUEUE, "Checked in", "Your booking has checked in at the centre.")
        db.flush()
        result = status_snapshot(db, booking)
    return result


def transition_queue(db: Session, actor: Principal, queue_id: str, payload: QueueActionInput):
    with serialized_write(db):
        entry = db.get(QueueEntry, queue_id)
        if entry is None:
            raise NotFound()
        booking = entry.booking
        centre_access(db, actor, booking.centre_id)
        if (entry.version != payload.expected_version or booking.status.value != entry.current_stage.value
                or booking.status in {BookingStatus.CANCELLED, BookingStatus.COMPLETED}
                or entry.checked_in_at is None):
            raise Conflict()
        action = payload.action
        if action == "hold":
            if entry.held:
                raise Conflict()
            entry.held = True
        elif action == "resume":
            if not entry.held:
                raise Conflict()
            entry.held = False
        else:
            if entry.held:
                raise Conflict()
            now = utc_now()
            if action == "advance" and entry.current_stage == QueueStage.CHECKED_IN:
                entry.current_stage, entry.quality_started_at = QueueStage.QUALITY_INSPECTION, now
            elif action == "advance" and entry.current_stage == QueueStage.QUALITY_INSPECTION:
                entry.current_stage, entry.weighing_started_at = QueueStage.WEIGHING, now
            elif action == "complete" and entry.current_stage == QueueStage.WEIGHING:
                entry.current_stage, entry.completed_at = QueueStage.COMPLETED, now
            else:
                raise Conflict()
            booking.status = BookingStatus(entry.current_stage.value)
        # Holds also update the booking revision, so stale booking readers detect the change.
        booking.updated_at = entry.updated_at = utc_now()
        titles = {"advance": "Stage advanced", "hold": "Booking held", "resume": "Booking resumed", "complete": "Booking completed"}
        notify_booking(db, booking, NoticeType.COMPLETED if action == "complete" else NoticeType.QUEUE,
            titles[action], "Current stage: " + booking.status.value + (". " + payload.reason if payload.reason else ""))
        db.flush()
        result = status_snapshot(db, booking)
    return result
