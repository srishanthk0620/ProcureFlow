from decimal import Decimal
from math import ceil
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base import utc_now
from app.models import Booking, ProcurementCentre, QueueEntry
from app.models.enums import BookingStatus, OperatingStatus, QueueStage
from app.schemas.eta import EtaRead
from app.services.resource_service import resources_snapshot

TERMINAL = (BookingStatus.COMPLETED, BookingStatus.CANCELLED)
REMAINING = {QueueStage.CHECKED_IN: Decimal(1), QueueStage.QUALITY_INSPECTION: Decimal(2) / 3,
             QueueStage.WEIGHING: Decimal(1) / 3, QueueStage.COMPLETED: Decimal(0)}


def ordered_queue(db: Session, centre_id: str) -> list[QueueEntry]:
    """Physical, nonheld, unfinished entries. Filters never change queue position."""
    return list(db.scalars(select(QueueEntry).join(Booking, QueueEntry.booking_id == Booking.id).where(
        QueueEntry.centre_id == centre_id, QueueEntry.held.is_(False),
        QueueEntry.checked_in_at.is_not(None), QueueEntry.current_stage != QueueStage.COMPLETED,
        Booking.status.not_in(TERMINAL)).order_by(QueueEntry.checked_in_at,
            Booking.appointment_date, Booking.start_time, QueueEntry.id)))


def remaining_quantity(entry: QueueEntry) -> Decimal:
    return entry.booking.quantity * REMAINING.get(entry.current_stage, Decimal(1))


def scheduled_workload(db: Session, centre_id, appointment_date, start_time, exclude_booking_id=None):
    query = select(Booking).where(Booking.centre_id == centre_id,
        Booking.appointment_date == appointment_date, Booking.start_time == start_time,
        Booking.status.not_in(TERMINAL))
    if exclude_booking_id is not None:
        query = query.where(Booking.id != exclude_booking_id)
    return sum((remaining_quantity(b.queue_entry) if b.queue_entry else b.quantity
        for b in db.scalars(query) if not (b.queue_entry and b.queue_entry.held)), Decimal(0))


def calculate_eta(db: Session, centre: ProcurementCentre, queued_quantity: Decimal,
                  processing_quantity: Decimal, travel: int | None, *, held=False,
                  done=False, available=True) -> EtaRead:
    factor, penalty, resources = resources_snapshot(db, centre)
    usable = available and factor > 0 and centre.is_active and centre.operating_status == OperatingStatus.OPEN
    if done:
        travel, queue, processing, penalty, total = 0, 0, 0, 0, 0
        reason = "Booking is terminal; no remaining work."
    elif not usable:
        queue, processing, total = None, None, None
        reason = "Unavailable capacity or centre; completion estimate is unknown."
    else:
        queue = None if held else ceil(queued_quantity * 10 / (Decimal(600) * factor))
        processing = ceil(processing_quantity * 10 / (Decimal(600) * factor))
        total = None if held or travel is None else travel + queue + processing + penalty
        reason = "Held; completion is unknown until Staff resumes work." if held else "Reference travel + remaining queued work + remaining processing + disruption delay."
    return EtaRead(travel_eta_minutes=travel, queue_eta_minutes=queue,
        processing_eta_minutes=processing, disruption_penalty_minutes=penalty,
        expected_completion_minutes=total, resource_factor=factor, resources=resources,
        calculated_at=utc_now(), reason=reason)


def booking_eta(db: Session, booking: Booking):
    entry = booking.queue_entry
    done = booking.status in TERMINAL
    physical = entry is not None and entry.checked_in_at is not None
    held = bool(entry and entry.held and not done)
    position = ahead = None
    if physical and not done:
        ordered = ordered_queue(db, booking.centre_id)
        index = next((i for i, e in enumerate(ordered) if e.id == entry.id), None)
        if index is not None:
            position, ahead = index + 1, index
            work = sum((remaining_quantity(e) for e in ordered[:index]), Decimal(0))
        else:
            work = Decimal(0)
        processing = remaining_quantity(entry)
    elif not done:
        # Scheduled workload only, not a claimed physical position; exclude this booking.
        work = scheduled_workload(db, booking.centre_id, booking.appointment_date, booking.start_time, booking.id)
        processing = booking.quantity
    else:
        work = processing = Decimal(0)
    eta = calculate_eta(db, booking.centre, work, processing,
        0 if physical else booking.centre.reference_travel_minutes, held=held, done=done)
    return eta, position, ahead
