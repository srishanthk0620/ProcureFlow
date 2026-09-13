from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Disruption, ProcurementCentre
from app.models.enums import DisruptionStatus, ResourceType
from app.schemas.eta import EffectiveResource

CRITICAL = (ResourceType.GATE, ResourceType.QUALITY_DESK, ResourceType.WEIGHBRIDGE, ResourceType.STAFF)


def resources_snapshot(db: Session, centre: ProcurementCentre):
    incidents = list(db.scalars(select(Disruption).where(Disruption.centre_id == centre.id,
        Disruption.status == DisruptionStatus.ACTIVE)))
    baseline = {r.resource_type: r for r in centre.resources}
    resources, fractions = [], []
    for kind in CRITICAL:
        item = baseline.get(kind)
        total, active = (item.total_count, item.active_count) if item else (0, 0)
        working = max(0, active - sum(d.resource_type == kind for d in incidents))
        fractions.append(Decimal(working) / total if total else Decimal(0))
        resources.append(EffectiveResource(resource_type=kind, total_count=total,
            baseline_active_count=active, effective_active_count=working))
    penalty = sum({"low": 5, "medium": 15, "high": 30}[d.severity.value] for d in incidents)
    return min(fractions), penalty, resources
