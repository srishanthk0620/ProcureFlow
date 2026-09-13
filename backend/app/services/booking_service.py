from typing import Protocol
from app.models import Booking
from app.schemas.core import BookingCreate
from app.services.auth_service import Principal


class BookingService(Protocol):
    """Implement owner checks and atomic capacity allocation before exposing APIs."""
    def create(self, actor: Principal, draft: BookingCreate) -> Booking: ...
    def cancel(self, actor: Principal, booking_id: str, expected_version: int) -> Booking: ...
