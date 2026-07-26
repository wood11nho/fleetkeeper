from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from fleetkeeper.models.base import Base, StringArray, TimestampMixin, enum_column
from fleetkeeper.models.enums import CategoryKind, CategorySection, IntervalSource
from fleetkeeper.models.vehicle import Vehicle


class ServiceCategory(Base, TimestampMixin):
    """One kind of work or obligation: an oil change, an inspection, an insurance policy.

    Rows with no garage are the built-in catalogue shared by everyone. Rows with a garage
    are that garage's own additions, so nobody is ever blocked by a catalogue that does
    not mention what they just had done.
    """

    __tablename__ = "service_categories"
    __table_args__ = (
        # Two built-in categories must not share a code even though both have a null
        # garage, which plain SQL uniqueness would happily allow.
        UniqueConstraint("garage_id", "code", postgresql_nulls_not_distinct=True),
        CheckConstraint(
            "default_interval_km is null or default_interval_km > 0",
            name="positive_km_interval",
        ),
        CheckConstraint(
            "default_interval_months is null or default_interval_months > 0",
            name="positive_month_interval",
        ),
        # An interval with no stated source is the thing this design exists to prevent:
        # a number the owner cannot weigh. The database refuses to store one.
        CheckConstraint(
            "(default_interval_km is null and default_interval_months is null)"
            " = (interval_source is null)",
            name="interval_needs_a_source",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int | None] = mapped_column(ForeignKey("garages.id", ondelete="CASCADE"))

    code: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(120))
    section: Mapped[CategorySection] = mapped_column(enum_column(CategorySection))
    kind: Mapped[CategoryKind] = mapped_column(enum_column(CategoryKind))

    default_interval_km: Mapped[int | None]
    default_interval_months: Mapped[int | None]
    interval_source: Mapped[IntervalSource | None] = mapped_column(enum_column(IntervalSource))

    requires_fuel_types: Mapped[StringArray]
    requires_gearbox_types: Mapped[StringArray]
    requires_drivetrains: Mapped[StringArray]
    requires_equipment: Mapped[StringArray]

    # Shown next to the item in the interface. Explains the reasoning behind an interval
    # so the owner can decide whether to follow it, shorten it, or turn the item off.
    hint: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    def applies_to(self, vehicle: Vehicle) -> bool:
        """An empty requirement means the item applies to every car."""
        if self.requires_fuel_types and vehicle.fuel_type not in self.requires_fuel_types:
            return False
        if self.requires_gearbox_types and vehicle.gearbox_type not in self.requires_gearbox_types:
            return False
        if self.requires_drivetrains and vehicle.drivetrain not in self.requires_drivetrains:
            return False
        return vehicle.has(*self.requires_equipment)
