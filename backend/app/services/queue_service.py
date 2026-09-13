from typing import Literal, Protocol
from app.models import QueueEntry
from app.services.auth_service import Principal

QueueAction = Literal["check_in", "advance", "hold", "resume", "complete"]


class QueueService(Protocol):
    """Future centre-scoped transitions; update booking, queue and notices atomically."""
    def transition(self, actor: Principal, entry_id: str, action: QueueAction,
                   expected_version: int) -> QueueEntry: ...
