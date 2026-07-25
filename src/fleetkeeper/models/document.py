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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fleetkeeper.models.base import Base, TimestampMixin
from fleetkeeper.models.catalog import ServiceCategory


class VehicleDocument(Base, TimestampMixin):
    """A paper obligation with a validity window: insurance, inspection, road tax.

    These are kept apart from service events because their deadline is not computed from
    an interval, it is printed on the document. The owner types both dates and the app
    only has to warn in time.
    """

    __tablename__ = "vehicle_documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["vehicle_id", "garage_id"],
            ["vehicles.id", "vehicles.garage_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("valid_to >= valid_from", name="validity_window_ordered"),
        CheckConstraint("cost is null or cost >= 0", name="non_negative_cost"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(index=True)
    vehicle_id: Mapped[int] = mapped_column(index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))

    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date] = mapped_column(Date, index=True)

    # The insurer for a policy, the testing station for an inspection.
    provider: Mapped[str | None] = mapped_column(String(120))
    reference_number: Mapped[str | None] = mapped_column(String(60))

    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RON", server_default=text("'RON'"))
    notes: Mapped[str | None] = mapped_column(Text)

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    category: Mapped[ServiceCategory] = relationship()
