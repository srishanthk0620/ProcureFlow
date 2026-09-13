from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from datetime import date, time
from math import ceil
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import ProcurementCentre, SlotPolicy
from app.schemas.farmer_api import CentreSummary, RecommendationRead
from app.services.centre_service import (get_commodity, list_centres, resource_capacity,
    slot_snapshot, validate_visit)


@dataclass(frozen=True)
class CentreEstimate:
    centre_id: str
    travel_minutes: int
    queue_minutes: int
    processing_minutes: int
    disruption_minutes: int
    explanation: str


class RecommendationService(Protocol):
    """Future deterministic ranking; no ORM computed properties or static demo waits."""
    def recommend(self, commodity_id: str, quantity: Decimal) -> list[CentreEstimate]: ...


def estimate_slot(db: Session, centre: ProcurementCentre, commodity, policy: SlotPolicy,
                  appointment_date: date, quantity: Decimal) -> RecommendationRead:
    """Single estimate boundary for recommendations and future booking ETA.

    Prototype workload model: 10 minutes per 600kg at full resource availability.
    Queue excludes terminal bookings and is scoped to the same centre/date/slot.
    """
    snapshot = slot_snapshot(db, centre, commodity, policy, appointment_date, quantity)
    factor, penalty = resource_capacity(db, centre)
    feasible = snapshot.available
    travel = centre.reference_travel_minutes
    queue = ceil(snapshot.booked_amount / Decimal(600) * 10 / factor) if feasible else None
    processing = ceil(quantity / Decimal(600) * 10 / factor) if feasible else None
    total = travel + queue + processing + penalty if feasible and travel is not None else None
    reason = ("Reference travel + same-slot queued workload + requested processing + disruption delay. "
              "Deterministic prototype estimate, not live navigation.") if feasible else "Unavailable: centre, resources, units or remaining slot capacity do not permit this quantity."
    if feasible and travel is None:
        reason = "Capacity available; travel reference missing, so completion ETA cannot be ranked."
    return RecommendationRead(centre=CentreSummary.model_validate(centre), start_time=policy.start_time,
        travel_eta_minutes=travel, queue_eta_minutes=queue, processing_eta_minutes=processing,
        disruption_penalty_minutes=penalty, expected_completion_minutes=total,
        reason=reason, capacity_available=feasible, remaining_capacity=snapshot.remaining_capacity)


def recommendations(db: Session, commodity: str, quantity: Decimal, appointment_date: date, start_time: time | None):
    validate_visit(appointment_date, quantity)
    item = get_commodity(db, commodity)
    output = []
    for centre in list_centres(db, commodity, None, None):
        query = select(SlotPolicy).where(SlotPolicy.centre_id == centre.id)
        if start_time is not None:
            query = query.where(SlotPolicy.start_time == start_time)
        estimates = [estimate_slot(db, centre, item, p, appointment_date, quantity) for p in db.scalars(query.order_by(SlotPolicy.start_time))]
        if estimates:
            output.append(min(estimates, key=lambda e: (e.expected_completion_minutes is None,
                e.expected_completion_minutes if e.expected_completion_minutes is not None else float("inf"), e.start_time)))
        else:
            output.append(RecommendationRead(centre=CentreSummary.model_validate(centre), start_time=None,
                travel_eta_minutes=centre.reference_travel_minutes, queue_eta_minutes=None,
                processing_eta_minutes=None, disruption_penalty_minutes=0, expected_completion_minutes=None,
                capacity_available=False, remaining_capacity=Decimal(0), reason="No persisted slot policy is available for this visit."))
    output.sort(key=lambda e: (e.expected_completion_minutes is None,
        e.expected_completion_minutes if e.expected_completion_minutes is not None else float("inf"), e.centre.code))
    if output and output[0].expected_completion_minutes is not None:
        output[0].recommended = True
    return output
