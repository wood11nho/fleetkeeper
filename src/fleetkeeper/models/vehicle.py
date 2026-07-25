from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fleetkeeper.models.base import Base, StringArray, TimestampMixin, enum_column
from fleetkeeper.models.enums import Drivetrain, FuelType, GearboxType
from fleetkeeper.models.garage import Garage


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"
    # Child tables reference this pair rather than the primary key alone, which lets the
    # database itself reject a record whose garage does not match its vehicle's garage.
    # Cross-garage leakage becomes impossible instead of merely unlikely.
    __table_args__ = (UniqueConstraint("id", "garage_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(ForeignKey("garages.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(60))
    make: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(60))
    generation: Mapped[str | None] = mapped_column(String(60))
    model_year: Mapped[int | None]
    registration_number: Mapped[str | None] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17))

    fuel_type: Mapped[FuelType] = mapped_column(enum_column(FuelType))
    engine_code: Mapped[str | None] = mapped_column(String(20))
    engine_displacement_cc: Mapped[int | None]
    power_hp: Mapped[int | None]

    gearbox_type: Mapped[GearboxType] = mapped_column(enum_column(GearboxType))
    gearbox_gears: Mapped[int | None]
    drivetrain: Mapped[Drivetrain] = mapped_column(enum_column(Drivetrain))

    equipment: Mapped[StringArray]

    # Romanian roadworthiness inspection falls due yearly rather than every two years
    # once a car is twelve years old, so the original registration date is not decoration.
    first_registration_date: Mapped[date | None] = mapped_column(Date)

    current_mileage_km: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    annual_mileage_km: Mapped[int | None]

    photo_storage_key: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    garage: Mapped[Garage] = relationship()

    def has(self, *equipment: str) -> bool:
        return all(item in self.equipment for item in equipment)
