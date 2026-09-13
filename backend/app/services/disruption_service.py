from typing import Protocol
from app.models import Disruption
from app.schemas.core import DisruptionCreate, DisruptionRead
from app.services.auth_service import Principal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import Conflict, NotFound
from app.db.base import utc_now
from app.db.transactions import serialized_write
from app.models import Booking, Notification, ProcurementCentre
from app.models.enums import BookingStatus, DisruptionStatus, NoticeType, ResourceType
from app.schemas.operations import IncidentInput, IncidentRead
from app.services.authorization import centre_access
from app.services.centre_service import local_today
from app.services.notification_service import notify_booking
from app.services.resource_service import resources_snapshot


class DisruptionService(Protocol):
    """Future resource checks and notifications. Recovery estimates never auto-resolve."""
    def report(self, actor: Principal, draft: DisruptionCreate) -> Disruption: ...
    def resolve(self, actor: Principal, disruption_id: str) -> Disruption: ...


def incident_read(incident: Disruption) -> IncidentRead:
    return IncidentRead(**DisruptionRead.model_validate(incident).model_dump(),
        updated_at=incident.resolved_at or incident.created_at, server_time=utc_now())


def list_disruptions(db: Session, actor: Principal, centre_id: str | None,
                     status: DisruptionStatus | None, limit: int, offset: int):
    assigned = centre_access(db, actor, centre_id)
    query = select(Disruption).where(Disruption.centre_id == assigned)
    if status is not None:
        query = query.where(Disruption.status == status)
    return [incident_read(d) for d in db.scalars(query.order_by(Disruption.created_at.desc(), Disruption.id).offset(offset).limit(limit))]


def report_disruption(db: Session, actor: Principal, payload: IncidentInput):
    with serialized_write(db):
        assigned = centre_access(db, actor, payload.centre_id)
        centre = db.get(ProcurementCentre, assigned)
        active = list(db.scalars(select(Disruption).where(Disruption.centre_id == assigned,
            Disruption.status == DisruptionStatus.ACTIVE, Disruption.resource_type == payload.resource_type)))
        # Each incident represents ONE DISTINCT unavailable unit. Replayed reports conflict.
        if any(d.note == payload.note for d in active):
            raise Conflict()
        if payload.resource_type != ResourceType.OTHER:
            _, _, resources = resources_snapshot(db, centre)
            resource = next((r for r in resources if r.resource_type == payload.resource_type), None)
            if resource is None or resource.effective_active_count <= 0:
                raise Conflict()
        incident = Disruption(centre_id=assigned, reported_by=actor.user_id,
            **payload.model_dump(exclude={"centre_id"}))
        db.add(incident)
        db.flush()
        if payload.severity.value in {"medium", "high"}:
            bookings = db.scalars(select(Booking).where(Booking.centre_id == assigned,
                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.COMPLETED]),
                (Booking.appointment_date >= local_today()) | Booking.queue_entry.has()))
            for booking in bookings:
                notify_booking(db, booking, NoticeType.DELAY, "Disruption " + incident.id,
                    "A " + incident.resource_type.value + " disruption affects your centre. Check your updated ETA.")
        db.flush()
        result = incident_read(incident)
    return result


def resolve_disruption(db: Session, actor: Principal, identifier: str):
    with serialized_write(db):
        incident = db.get(Disruption, identifier)
        if incident is None:
            raise NotFound()
        centre_access(db, actor, incident.centre_id)
        if incident.status != DisruptionStatus.ACTIVE:
            raise Conflict()
        incident.status, incident.resolved_at = DisruptionStatus.RESOLVED, utc_now()
        # Notify only bookings that received this incident's original notice.
        ids = select(Notification.booking_id).where(Notification.category == NoticeType.DELAY,
            Notification.title == "Disruption " + incident.id)
        for booking in db.scalars(select(Booking).where(Booking.id.in_(ids),
                Booking.status.not_in([BookingStatus.CANCELLED, BookingStatus.COMPLETED]))):
            notify_booking(db, booking, NoticeType.QUEUE, "Disruption resolved",
                "Disruption " + incident.id + " is resolved. Your centre ETA has been refreshed.")
        db.flush()
        result = incident_read(incident)
    return result
