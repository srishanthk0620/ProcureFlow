from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (Boolean, CheckConstraint, Column, Date, DateTime, Enum,
    ForeignKey, ForeignKeyConstraint, Integer, Numeric, String, Table, Time, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Identity, Timestamps, utc_now
from app.models.enums import (BookingStatus, DisruptionStatus, GrievanceCategory,
    GrievanceStatus, NoticeType, OperatingStatus, QueueStage, ResourceType, RoleName, Severity)


def enum_type(cls):
    return Enum(cls, values_callable=lambda e: [x.value for x in e],
                native_enum=False, create_constraint=True, validate_strings=True,
                name=cls.__name__.lower())


class User(Identity, Timestamps, Base):
    __tablename__ = "users"
    display_name: Mapped[str] = mapped_column(String(120))
    mobile: Mapped[str | None] = mapped_column(String(20), unique=True)
    login_name: Mapped[str | None] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    roles: Mapped[list[Role]] = relationship(secondary="user_roles")
    farmer_profile: Mapped[FarmerProfile | None] = relationship(back_populates="user", uselist=False)
    staff_profile: Mapped[StaffProfile | None] = relationship(back_populates="user", uselist=False)


class Role(Identity, Base):
    __tablename__ = "roles"
    name: Mapped[RoleName] = mapped_column(enum_type(RoleName), unique=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), primary_key=True)


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    user: Mapped[User] = relationship(back_populates="farmer_profile")


class StaffProfile(Base):
    __tablename__ = "staff_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(40), unique=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    user: Mapped[User] = relationship(back_populates="staff_profile")
    centre: Mapped[ProcurementCentre] = relationship()


centre_commodities = Table("centre_commodities", Base.metadata,
    Column("centre_id", ForeignKey("centres.id"), primary_key=True),
    Column("commodity_id", ForeignKey("commodities.id"), primary_key=True))


class ProcurementCentre(Identity, Timestamps, Base):
    __tablename__ = "centres"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        CheckConstraint("reference_travel_minutes >= 0", name="travel_nonnegative"),
        CheckConstraint("reference_distance_km >= 0", name="distance_nonnegative"),
    )
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    district: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(80))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    operating_status: Mapped[OperatingStatus] = mapped_column(enum_type(OperatingStatus), default=OperatingStatus.OPEN)
    reference_travel_minutes: Mapped[int | None] = mapped_column(Integer)
    reference_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    commodities: Mapped[list[Commodity]] = relationship(secondary=centre_commodities)
    resources: Mapped[list[CentreResource]] = relationship(back_populates="centre")


class Commodity(Identity, Base):
    __tablename__ = "commodities"
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), default="kg")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CentreResource(Identity, Base):
    __tablename__ = "centre_resources"
    __table_args__ = (UniqueConstraint("centre_id", "resource_type"),
        CheckConstraint("total_count >= 0 AND active_count >= 0 AND active_count <= total_count", name="valid_counts"))
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"))
    resource_type: Mapped[ResourceType] = mapped_column(enum_type(ResourceType))
    total_count: Mapped[int] = mapped_column(Integer)
    active_count: Mapped[int] = mapped_column(Integer)
    centre: Mapped[ProcurementCentre] = relationship(back_populates="resources")


class Booking(Identity, Timestamps, Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("id", "centre_id"),
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("version > 0", name="positive_version"),
        CheckConstraint("(status = 'cancelled' AND cancelled_at IS NOT NULL) OR (status <> 'cancelled' AND cancelled_at IS NULL AND cancellation_reason IS NULL)", name="cancellation_consistency"))
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmer_profiles.user_id"), index=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    commodity_id: Mapped[str] = mapped_column(ForeignKey("commodities.id"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[time] = mapped_column(Time)
    token: Mapped[str] = mapped_column(String(60), unique=True)
    status: Mapped[BookingStatus] = mapped_column(enum_type(BookingStatus), default=BookingStatus.BOOKED)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500))
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}
    farmer: Mapped[FarmerProfile] = relationship()
    centre: Mapped[ProcurementCentre] = relationship()
    commodity: Mapped[Commodity] = relationship()
    group_metadata: Mapped[BookingGroupMetadata | None] = relationship(back_populates="booking", uselist=False)
    queue_entry: Mapped[QueueEntry | None] = relationship(back_populates="booking", uselist=False)


class BookingGroupMetadata(Base):
    __tablename__ = "booking_group_metadata"
    __table_args__ = (CheckConstraint("farmer_count BETWEEN 2 AND 20", name="farmer_count_range"),)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), primary_key=True)
    group_name: Mapped[str] = mapped_column(String(60))
    farmer_count: Mapped[int] = mapped_column(Integer)
    contact_name: Mapped[str] = mapped_column(String(60))
    booking: Mapped[Booking] = relationship(back_populates="group_metadata")


class QueueEntry(Identity, Base):
    __tablename__ = "queue_entries"
    __table_args__ = (ForeignKeyConstraint(["booking_id", "centre_id"], ["bookings.id", "bookings.centre_id"]),
        CheckConstraint("position IS NULL OR position >= 1", name="positive_position"),
        CheckConstraint("version > 0", name="positive_version"))
    booking_id: Mapped[str] = mapped_column(String(36), unique=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    current_stage: Mapped[QueueStage] = mapped_column(enum_type(QueueStage), default=QueueStage.BOOKED)
    held: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int | None] = mapped_column(Integer)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime)
    quality_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    weighing_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}
    booking: Mapped[Booking] = relationship(back_populates="queue_entry")


class Disruption(Identity, Base):
    __tablename__ = "disruptions"
    __table_args__ = (CheckConstraint("expected_recovery_minutes BETWEEN 5 AND 480", name="recovery_range"),
        CheckConstraint("(status = 'active' AND resolved_at IS NULL) OR (status = 'resolved' AND resolved_at IS NOT NULL AND resolved_at >= created_at)", name="resolution_consistency"))
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    resource_type: Mapped[ResourceType] = mapped_column(enum_type(ResourceType))
    severity: Mapped[Severity] = mapped_column(enum_type(Severity))
    note: Mapped[str] = mapped_column(String(300))
    expected_recovery_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[DisruptionStatus] = mapped_column(enum_type(DisruptionStatus), default=DisruptionStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    reported_by: Mapped[str] = mapped_column(ForeignKey("staff_profiles.user_id"))
    centre: Mapped[ProcurementCentre] = relationship()
    reporter: Mapped[StaffProfile] = relationship()


class Notification(Identity, Base):
    __tablename__ = "notifications"
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[NoticeType] = mapped_column(enum_type(NoticeType))
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(String(1000))
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    recipient: Mapped[User] = relationship()
    booking: Mapped[Booking | None] = relationship()


class Grievance(Identity, Timestamps, Base):
    __tablename__ = "grievances"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[GrievanceCategory] = mapped_column(enum_type(GrievanceCategory))
    description: Mapped[str] = mapped_column(String(500))
    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"))
    centre_id: Mapped[str | None] = mapped_column(ForeignKey("centres.id"))
    reference: Mapped[str] = mapped_column(String(60), unique=True)
    status: Mapped[GrievanceStatus] = mapped_column(enum_type(GrievanceStatus), default=GrievanceStatus.SUBMITTED)
    user: Mapped[User] = relationship()
    booking: Mapped[Booking | None] = relationship()
    centre: Mapped[ProcurementCentre | None] = relationship()


class PriceRecord(Identity, Base):
    __tablename__ = "price_records"
    __table_args__ = (CheckConstraint("rate > 0", name="positive_rate"),)
    commodity_id: Mapped[str] = mapped_column(ForeignKey("commodities.id"), index=True)
    centre_id: Mapped[str | None] = mapped_column(ForeignKey("centres.id"))
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit: Mapped[str] = mapped_column(String(20))
    effective_date: Mapped[date] = mapped_column(Date)
    source_label: Mapped[str] = mapped_column(String(160))
    illustrative: Mapped[bool] = mapped_column(Boolean, default=True)
    commodity: Mapped[Commodity] = relationship()
    centre: Mapped[ProcurementCentre | None] = relationship()
