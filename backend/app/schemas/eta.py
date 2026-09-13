from datetime import datetime
from decimal import Decimal
from app.schemas.core import Read
from app.models.enums import ResourceType


class EffectiveResource(Read):
    resource_type: ResourceType
    total_count: int
    baseline_active_count: int
    effective_active_count: int


class EtaRead(Read):
    travel_eta_minutes: int | None
    queue_eta_minutes: int | None
    processing_eta_minutes: int | None
    disruption_penalty_minutes: int
    expected_completion_minutes: int | None
    resource_factor: Decimal
    resources: list[EffectiveResource]
    calculated_at: datetime
    reason: str
