from typing import Protocol
from app.models import Disruption
from app.schemas.core import DisruptionCreate
from app.services.auth_service import Principal


class DisruptionService(Protocol):
    """Future resource checks and notifications. Recovery estimates never auto-resolve."""
    def report(self, actor: Principal, draft: DisruptionCreate) -> Disruption: ...
    def resolve(self, actor: Principal, disruption_id: str) -> Disruption: ...
