from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.enums import (BookingStatus, DisruptionStatus, GrievanceCategory,
    GrievanceStatus, NoticeType, OperatingStatus, QueueStage, ResourceType, RoleName, Severity)

Identifier = Annotated[str, Field(min_length=1, max_length=36)]
Quantity = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=3)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Read(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json")
    def serialize_utc(self, value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return value


class RoleRead(Read):
    name: RoleName


class UserRead(Read):
    id: str
    display_name: str
    is_active: bool
    roles: list[RoleRead]
    # Password hashes, login identifiers and mobile numbers are not public reads.


class CommodityRead(Read):
    id: str
    code: str
    name: str
    unit: str
    is_active: bool


class ResourceRead(Read):
    id: str
    resource_type: ResourceType
    total_count: int
    active_count: int


class CentreRead(Read):
    id: str
    code: str
    name: str
    district: str
    state: str
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool
    operating_status: OperatingStatus
    reference_travel_minutes: int | None
    reference_distance_km: Decimal | None
    commodities: list[CommodityRead]
    resources: list[ResourceRead]


class GroupInput(Input):
    group_name: str = Field(min_length=1, max_length=60)
    farmer_count: int = Field(ge=2, le=20, strict=True)
    contact_name: str = Field(min_length=1, max_length=60)


class GroupRead(Read):
    group_name: str
    farmer_count: int
    contact_name: str


class BookingCreate(Input):
    centre_id: Identifier
    commodity_id: Identifier
    quantity: Quantity
    appointment_date: date
    start_time: time
    group_metadata: GroupInput | None = None
    # Owner, token, status, version and capacity decisions are server-owned.


class BookingRead(Read):
    id: str
    farmer_id: str
    centre_id: str
    commodity_id: str
    quantity: Decimal
    appointment_date: date
    start_time: time
    token: str
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None
    cancellation_reason: str | None
    version: int
    group_metadata: GroupRead | None


class QueueRead(Read):
    id: str
    booking_id: str
    centre_id: str
    current_stage: QueueStage
    held: bool
    position: int | None
    checked_in_at: datetime | None
    quality_started_at: datetime | None
    weighing_started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    version: int


class DisruptionCreate(Input):
    centre_id: Identifier
    resource_type: ResourceType
    severity: Severity
    note: str = Field(min_length=1, max_length=300)
    expected_recovery_minutes: int = Field(ge=5, le=480, strict=True)


class DisruptionRead(Read):
    id: str
    centre_id: str
    resource_type: ResourceType
    severity: Severity
    note: str
    expected_recovery_minutes: int
    status: DisruptionStatus
    created_at: datetime
    resolved_at: datetime | None
    reported_by: str


class NotificationRead(Read):
    id: str
    category: NoticeType
    title: str
    message: str
    booking_id: str | None
    is_read: bool
    created_at: datetime


class GrievanceCreate(Input):
    category: GrievanceCategory
    description: str = Field(min_length=10, max_length=500)
    booking_id: Identifier | None = None
    centre_id: Identifier | None = None


class GrievanceRead(Read):
    id: str
    user_id: str
    category: GrievanceCategory
    description: str
    booking_id: str | None
    centre_id: str | None
    reference: str
    status: GrievanceStatus
    created_at: datetime
    updated_at: datetime


class PriceRead(Read):
    id: str
    commodity_id: str
    centre_id: str | None
    rate: Decimal
    unit: str
    effective_date: date
    source_label: str
    illustrative: bool
