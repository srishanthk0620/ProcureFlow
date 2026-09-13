"""Import all models so migrations see the complete metadata."""
from app.models.identity import AuthSession, OtpChallenge, SlotPolicy, StaffAuthAttempt
from app.models.entities import (Booking, BookingGroupMetadata, CentreResource,
    Commodity, Disruption, FarmerProfile, Grievance, Notification, PriceRecord,
    ProcurementCentre, QueueEntry, Role, StaffProfile, User, UserRole)

__all__ = ["StaffAuthAttempt", "AuthSession", "OtpChallenge", "SlotPolicy", "Booking", "BookingGroupMetadata", "CentreResource", "Commodity",
    "Disruption", "FarmerProfile", "Grievance", "Notification", "PriceRecord",
    "ProcurementCentre", "QueueEntry", "Role", "StaffProfile", "User", "UserRole"]
