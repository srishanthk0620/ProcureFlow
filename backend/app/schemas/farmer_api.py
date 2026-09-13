from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal
from pydantic import ConfigDict, Field
from app.schemas.core import Input, Read, UserRead, BookingRead, CommodityRead, Quantity


class MobileRequest(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    mobile: str = Field(pattern=r"^[0-9]{10}$", min_length=10, max_length=10, strict=True)


class OtpVerify(Input):
    challenge_id: str = Field(min_length=36, max_length=36)
    otp: str = Field(pattern=r"^[0-9]{6}$", min_length=6, max_length=6, strict=True)


class ChallengeRead(Read):
    challenge_id: str
    expires_at: datetime
    retry_after_seconds: int
    development_otp: str | None = None


class FarmerProfileRead(Read):
    district: str
    state: str


class IdentityRead(Read):
    user: UserRead
    farmer_profile: FarmerProfileRead | None


class SessionRead(IdentityRead):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime


class CancelRequest(Input):
    expected_version: int = Field(gt=0, strict=True)
    reason: str | None = Field(default=None, min_length=1, max_length=500)


class CentreSummary(Read):
    id: str
    code: str
    name: str


class BookingDetail(BookingRead):
    centre: CentreSummary
    commodity: CommodityRead


class SlotRead(Read):
    start_time: time
    end_time: time
    capacity: Decimal
    booked_amount: Decimal
    remaining_capacity: Decimal
    unit: str
    available: bool


class RecommendationRead(Read):
    centre: CentreSummary
    start_time: time | None
    travel_eta_minutes: int | None
    queue_eta_minutes: int | None
    processing_eta_minutes: int | None
    disruption_penalty_minutes: int
    expected_completion_minutes: int | None
    recommended: bool = False
    reason: str
    capacity_available: bool
    remaining_capacity: Decimal
    travel_source: str = "Persisted reference estimate; no live GPS or traffic"
