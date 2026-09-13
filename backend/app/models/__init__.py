"""Import all models so migrations see the complete metadata."""
from app.models.entities import (Booking, BookingGroupMetadata, CentreResource,
    Commodity, Disruption, FarmerProfile, Grievance, Notification, PriceRecord,
    ProcurementCentre, QueueEntry, Role, StaffProfile, User, UserRole)

__all__ = ["Booking", "BookingGroupMetadata", "CentreResource", "Commodity",
    "Disruption", "FarmerProfile", "Grievance", "Notification", "PriceRecord",
    "ProcurementCentre", "QueueEntry", "Role", "StaffProfile", "User", "UserRole"]
