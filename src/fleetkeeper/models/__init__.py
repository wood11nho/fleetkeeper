"""Importing every model here is what lets Alembic see the full schema.

Without it, autogenerate compares the database against whichever models happen to have
been imported and cheerfully proposes dropping the rest.
"""

from fleetkeeper.models.attachment import Attachment
from fleetkeeper.models.base import Base
from fleetkeeper.models.catalog import ServiceCategory
from fleetkeeper.models.document import VehicleDocument
from fleetkeeper.models.fuel import FuelLog, MileageReading
from fleetkeeper.models.garage import Garage, GarageInvitation, GarageMember
from fleetkeeper.models.maintenance import MaintenanceRule, ServiceEvent, ServiceEventItem
from fleetkeeper.models.operations import JobRun, NotificationLog
from fleetkeeper.models.session import UserSession
from fleetkeeper.models.user import User
from fleetkeeper.models.vehicle import Vehicle

__all__ = [
    "Attachment",
    "Base",
    "FuelLog",
    "Garage",
    "GarageInvitation",
    "GarageMember",
    "JobRun",
    "MaintenanceRule",
    "MileageReading",
    "NotificationLog",
    "ServiceCategory",
    "ServiceEvent",
    "ServiceEventItem",
    "User",
    "UserSession",
    "Vehicle",
    "VehicleDocument",
]
