from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal
from pydantic import Field
from app.models.enums import BookingStatus, ResourceType, Severity
from app.schemas.core import Input, Read, CommodityRead, DisruptionRead, NotificationRead
from app.schemas.eta import EtaRead
from app.schemas.farmer_api import CentreSummary


class VersionAction(Input):
    expected_version: int = Field(gt=0, strict=True)
    reason: str | None = Field(default=None, min_length=1, max_length=300)


class QueueActionInput(VersionAction):
    action: Literal["advance", "hold", "resume", "complete"]


class FarmerSummary(Read):
    display_name: str


class QueueStatus(Read):
    booking_id: str
    token: str
    centre: CentreSummary
    farmer: FarmerSummary
    commodity: CommodityRead
    quantity: Decimal
    appointment_date: date
    start_time: time
    queue_id: str | None
    checked_in: bool
    current_stage: BookingStatus
    held: bool
    position: int | None
    bookings_ahead: int | None
    checked_in_at: datetime | None
    quality_started_at: datetime | None
    weighing_started_at: datetime | None
    completed_at: datetime | None
    version: int
    booking_version: int
    updated_at: datetime
    server_time: datetime
    stale: bool = False
    eta: EtaRead


class IncidentInput(Input):
    centre_id: str | None = Field(default=None, min_length=1, max_length=36)
    resource_type: ResourceType
    severity: Severity
    note: str = Field(min_length=1, max_length=300)
    expected_recovery_minutes: int = Field(ge=5, le=480, strict=True)


class IncidentRead(DisruptionRead):
    updated_at: datetime
    server_time: datetime


class NotificationUpdate(Input):
    read: bool = Field(strict=True)
