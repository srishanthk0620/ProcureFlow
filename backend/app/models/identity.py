from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, Identity, utc_now


class AuthSession(Identity, Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (CheckConstraint("auth_method IN ('farmer_otp', 'staff_otp')", name="valid_auth_method"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    environment: Mapped[str] = mapped_column(String(30))
    auth_method: Mapped[str] = mapped_column(String(20), default="farmer_otp", server_default="farmer_otp")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class OtpChallenge(Identity, Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (CheckConstraint("attempts BETWEEN 0 AND 5", name="attempt_range"),)
    mobile: Mapped[str] = mapped_column(String(10), index=True)
    otp_digest: Mapped[str] = mapped_column(String(64))
    environment: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime)


class SlotPolicy(Identity, Base):
    """Recurring daily quantity limit; shared across supported commodities of the same unit."""
    __tablename__ = "slot_policies"
    __table_args__ = (UniqueConstraint("centre_id", "start_time"),
        CheckConstraint("capacity > 0", name="positive_capacity"),
        CheckConstraint("end_time > start_time", name="valid_time_range"))
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    capacity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit: Mapped[str] = mapped_column(String(20), default="kg")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StaffAuthAttempt(Identity, Base):
    """A persisted password attempt; successful attempts also carry an OTP challenge."""
    __tablename__ = "staff_auth_attempts"
    __table_args__ = (CheckConstraint("attempts BETWEEN 0 AND 5", name="attempt_range"),)
    identifier_digest: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    otp_digest: Mapped[str | None] = mapped_column(String(64))
    credential_digest: Mapped[str | None] = mapped_column(String(64))
    environment: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime)
