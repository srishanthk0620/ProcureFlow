from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


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
