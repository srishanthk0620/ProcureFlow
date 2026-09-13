from enum import StrEnum


class RoleName(StrEnum):
    FARMER = "farmer"
    STAFF = "staff"
    CENTRE_MANAGER = "centre_manager"
    DELEGATE = "delegate"
    DISTRICT_ADMIN = "district_admin"
    STATE_ADMIN = "state_admin"
    SUPER_ADMIN = "super_admin"


class OperatingStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class ResourceType(StrEnum):
    GATE = "gate"
    QUALITY_DESK = "quality_desk"
    WEIGHBRIDGE = "weighbridge"
    STAFF = "staff"
    OTHER = "other"


class BookingStatus(StrEnum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    QUALITY_INSPECTION = "quality_inspection"
    WEIGHING = "weighing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QueueStage(StrEnum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    QUALITY_INSPECTION = "quality_inspection"
    WEIGHING = "weighing"
    COMPLETED = "completed"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DisruptionStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class NoticeType(StrEnum):
    CONFIRMED = "confirmed"
    REMINDER = "reminder"
    QUEUE = "queue"
    DELAY = "delay"
    COMPLETED = "completed"
    GRIEVANCE = "grievance"
    CANCELLED = "cancelled"


class GrievanceCategory(StrEnum):
    BOOKINGS = "bookings"
    CENTRE = "centre"
    QUALITY = "quality"
    OTHER = "other"


class GrievanceStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
