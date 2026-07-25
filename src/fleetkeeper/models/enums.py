from enum import StrEnum


class FuelType(StrEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    PETROL_LPG = "petrol_lpg"
    HYBRID_PETROL = "hybrid_petrol"
    HYBRID_DIESEL = "hybrid_diesel"
    PLUGIN_HYBRID = "plugin_hybrid"
    ELECTRIC = "electric"


class GearboxType(StrEnum):
    MANUAL = "manual"
    TORQUE_CONVERTER = "torque_converter"
    DUAL_CLUTCH_DRY = "dual_clutch_dry"
    DUAL_CLUTCH_WET = "dual_clutch_wet"
    CVT = "cvt"


class Drivetrain(StrEnum):
    FRONT = "front"
    REAR = "rear"
    ALL = "all"


class Equipment(StrEnum):
    """Optional hardware that decides whether a catalogue item applies to a car.

    A timing belt needs replacing on a schedule and a timing chain does not; a car
    without a particulate filter never needs one cleaned. Modelling these as data
    rather than as branches in code means adding a new rule is a row, not a release.
    """

    TIMING_BELT = "timing_belt"
    PARTICULATE_FILTER = "particulate_filter"
    ADBLUE = "adblue"
    LPG_SYSTEM = "lpg_system"
    AIR_SUSPENSION = "air_suspension"
    AIR_CONDITIONING = "air_conditioning"


class CategorySection(StrEnum):
    DOCUMENTS = "documents"
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    RUNNING_GEAR = "running_gear"
    ELECTRICAL = "electrical"
    OTHER = "other"


class CategoryKind(StrEnum):
    """Maintenance items recur on an interval; documents expire on a fixed date."""

    MAINTENANCE = "maintenance"
    DOCUMENT = "document"


class MileageSource(StrEnum):
    MANUAL = "manual"
    FUEL_LOG = "fuel_log"
    SERVICE_EVENT = "service_event"


class NotificationStatus(StrEnum):
    SENT = "sent"
    FAILED = "failed"


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
