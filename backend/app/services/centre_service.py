from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.core.errors import InvalidRequest, NotFound
from app.models import Booking, Commodity, ProcurementCentre, SlotPolicy, Disruption
from app.models.enums import BookingStatus, DisruptionStatus, OperatingStatus, ResourceType
from app.schemas.farmer_api import SlotRead

TERMINAL = (BookingStatus.CANCELLED, BookingStatus.COMPLETED)
CRITICAL = (ResourceType.GATE, ResourceType.QUALITY_DESK, ResourceType.WEIGHBRIDGE, ResourceType.STAFF)


def local_today() -> date:
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def validate_visit(appointment_date: date, quantity: Decimal):
    if not local_today() + timedelta(days=1) <= appointment_date <= local_today() + timedelta(days=7) or not quantity.is_finite() or quantity < 50 or quantity > 20000 or quantity != quantity.to_integral_value():
        raise InvalidRequest()


def get_commodity(db: Session, value: str) -> Commodity:
    commodity = db.scalar(select(Commodity).where(or_(Commodity.id == value, Commodity.code == value)))
    if commodity is None:
        raise NotFound()
    if not commodity.is_active:
        raise InvalidRequest()
    return commodity


def get_centre(db: Session, value: str) -> ProcurementCentre:
    centre = db.get(ProcurementCentre, value)
    if centre is None:
        raise NotFound()
    return centre


def list_centres(db: Session, commodity: str | None, district: str | None, active: bool | None):
    query = select(ProcurementCentre).order_by(ProcurementCentre.code)
    if commodity is not None:
        item = get_commodity(db, commodity)
        query = query.where(ProcurementCentre.commodities.any(Commodity.id == item.id))
    if district is not None:
        query = query.where(ProcurementCentre.district == district)
    if active is not None:
        query = query.where(ProcurementCentre.is_active == active)
    return list(db.scalars(query))


def resource_capacity(db: Session, centre: ProcurementCentre) -> tuple[Decimal, int]:
    incidents = list(db.scalars(select(Disruption).where(Disruption.centre_id == centre.id,
        Disruption.status == DisruptionStatus.ACTIVE)))
    resources = {r.resource_type: r for r in centre.resources}
    fractions = []
    for kind in CRITICAL:
        resource = resources.get(kind)
        if resource is None or resource.total_count <= 0:
            fractions.append(Decimal(0))
        else:
            working = max(0, resource.active_count - sum(d.resource_type == kind for d in incidents))
            fractions.append(Decimal(working) / resource.total_count)
    penalty = sum({"low": 5, "medium": 15, "high": 30}[d.severity.value] for d in incidents)
    return min(fractions), penalty


def booked_amount(db: Session, centre_id: str, appointment_date: date, start_time: time) -> Decimal:
    return Decimal(db.scalar(select(func.coalesce(func.sum(Booking.quantity), 0)).where(
        Booking.centre_id == centre_id, Booking.appointment_date == appointment_date,
        Booking.start_time == start_time, Booking.status.not_in(TERMINAL))))


def slot_snapshot(db: Session, centre: ProcurementCentre, commodity: Commodity,
                  policy: SlotPolicy, appointment_date: date, quantity: Decimal) -> SlotRead:
    factor, _ = resource_capacity(db, centre)
    eligible = centre.is_active and centre.operating_status == OperatingStatus.OPEN and commodity in centre.commodities
    # Mixed units are never silently summed against the same quantity budget.
    compatible = policy.unit == commodity.unit and all(c.unit == policy.unit for c in centre.commodities)
    capacity = (policy.capacity * factor).quantize(Decimal("0.001"), rounding=ROUND_FLOOR) if eligible and compatible and policy.is_active else Decimal(0)
    used = booked_amount(db, centre.id, appointment_date, policy.start_time)
    remaining = max(Decimal(0), capacity - used)
    return SlotRead(start_time=policy.start_time, end_time=policy.end_time, capacity=capacity,
        booked_amount=used, remaining_capacity=remaining, unit=policy.unit,
        available=remaining >= quantity and capacity > 0)


def slots(db: Session, centre_id: str, appointment_date: date, commodity: str, quantity: Decimal):
    validate_visit(appointment_date, quantity)
    centre, item = get_centre(db, centre_id), get_commodity(db, commodity)
    if item not in centre.commodities:
        raise InvalidRequest()
    policies = db.scalars(select(SlotPolicy).where(SlotPolicy.centre_id == centre_id).order_by(SlotPolicy.start_time))
    return [slot_snapshot(db, centre, item, policy, appointment_date, quantity) for policy in policies]
