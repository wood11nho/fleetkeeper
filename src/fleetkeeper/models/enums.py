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
    """How a deadline for this kind of item comes about."""

    # Replaced or serviced on a schedule: oil, filters, timing belt.
    MAINTENANCE = "maintenance"

    # Wear parts, which have no honest replacement schedule. Brake pads last one summer
    # of mountain driving or four years of commuting, so the interval says how often to
    # look, and replacement is recorded whenever measurement says it is due.
    INSPECTION = "inspection"

    # Expires on a printed date: insurance, roadworthiness, road tax.
    DOCUMENT = "document"


class IntervalSource(StrEnum):
    """Where an interval comes from, shown next to it so its weight is visible.

    A figure the manufacturer publishes and a figure someone in a workshop finds
    reasonable are both useful, but they are not the same claim, and presenting them
    identically invites the owner to trust the weaker one too much.
    """

    # Published service schedule for this class of engine.
    MANUFACTURER = "manufacturer"

    # Widely used workshop convention, often where the manufacturer says "lifetime".
    PRACTICE = "practice"

    # A rough default with no authority behind it. Verify by measurement or manual.
    ESTIMATE = "estimate"


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
