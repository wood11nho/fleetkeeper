from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from fleetkeeper.models.base import Base, TimestampMixin, enum_column
from fleetkeeper.models.enums import MileageSource


class FuelLog(Base, TimestampMixin):
    """One visit to a filling station.

    Consumption is only meaningful between two full tanks, so whether the tank was filled
    to the brim is recorded rather than assumed.
    """

    __tablename__ = "fuel_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["vehicle_id", "garage_id"],
            ["vehicles.id", "vehicles.garage_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("litres > 0", name="positive_litres"),
        CheckConstraint("mileage_km >= 0", name="non_negative_mileage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(index=True)
    vehicle_id: Mapped[int] = mapped_column(index=True)

    filled_on: Mapped[date] = mapped_column(Date)
    mileage_km: Mapped[int]
    litres: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    price_per_litre: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RON", server_default=text("'RON'"))

    is_full_tank: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    station: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class MileageReading(Base, TimestampMixin):
    """An odometer value on a date.

    The history of these readings is what turns a mileage threshold into a calendar date:
    the average distance covered per day says roughly when the next service falls due,
    which is the only way a reminder can arrive before the fact rather than after it.
    """

    __tablename__ = "mileage_readings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["vehicle_id", "garage_id"],
            ["vehicles.id", "vehicles.garage_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("mileage_km >= 0", name="non_negative_mileage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(index=True)
    vehicle_id: Mapped[int] = mapped_column(index=True)

    recorded_on: Mapped[date] = mapped_column(Date, index=True)
    mileage_km: Mapped[int]
    source: Mapped[MileageSource] = mapped_column(enum_column(MileageSource))

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
