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
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fleetkeeper.models.base import Base, TimestampMixin
from fleetkeeper.models.catalog import ServiceCategory


class MaintenanceRule(Base, TimestampMixin):
    """The interval this particular car follows for one catalogue item.

    Created from the catalogue defaults when a vehicle is added, then owned by the user:
    a diesel driven in city traffic can have its oil interval shortened without that
    decision leaking into anyone else's car.
    """

    __tablename__ = "maintenance_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["vehicle_id", "garage_id"],
            ["vehicles.id", "vehicles.garage_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("vehicle_id", "category_id"),
        CheckConstraint("interval_km is null or interval_km > 0", name="positive_km_interval"),
        CheckConstraint(
            "interval_months is null or interval_months > 0", name="positive_month_interval"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(index=True)
    vehicle_id: Mapped[int] = mapped_column(index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))

    interval_km: Mapped[int | None]
    interval_months: Mapped[int | None]
    is_enabled: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    category: Mapped[ServiceCategory] = relationship()


class ServiceEvent(Base, TimestampMixin):
    """Something that was done to a car on a given day.

    Only the vehicle, the category and the date are required. Mileage, cost, workshop and
    parts are all optional, because a record written from memory months later is still
    worth far more than no record at all.
    """

    __tablename__ = "service_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["vehicle_id", "garage_id"],
            ["vehicles.id", "vehicles.garage_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("mileage_km is null or mileage_km >= 0", name="non_negative_mileage"),
        CheckConstraint("cost is null or cost >= 0", name="non_negative_cost"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(index=True)
    vehicle_id: Mapped[int] = mapped_column(index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))

    performed_on: Mapped[date] = mapped_column(Date)
    mileage_km: Mapped[int | None]
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RON", server_default=text("'RON'"))
    workshop: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    category: Mapped[ServiceCategory] = relationship()
    items: Mapped[list["ServiceEventItem"]] = relationship(
        back_populates="service_event", cascade="all, delete-orphan"
    )


class ServiceEventItem(Base):
    """A part or fluid used during a service event, recorded when the owner cares to.

    Knowing that last time the oil was Castrol 5W-30 and the filter was a Mann saves a
    phone call to the workshop next time.
    """

    __tablename__ = "service_event_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_quantity"),
        CheckConstraint("unit_cost is null or unit_cost >= 0", name="non_negative_unit_cost"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_event_id: Mapped[int] = mapped_column(
        ForeignKey("service_events.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(120))
    brand: Mapped[str | None] = mapped_column(String(60))
    part_number: Mapped[str | None] = mapped_column(String(60))
    quantity: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=1, server_default=text("1"))
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    service_event: Mapped[ServiceEvent] = relationship(back_populates="items")
