from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from fleetkeeper.models.base import Base


class Attachment(Base):
    """A scanned document or photograph stored in object storage.

    Only metadata lives here; the file itself sits in a bucket, keyed by storage_key. A
    nullable foreign key per owner type rather than a generic type-and-id pair means the
    database still enforces referential integrity and still cascades deletes, so removing
    a service event cannot leave its invoice orphaned.
    """

    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "(vehicle_id is not null)::int"
            " + (service_event_id is not null)::int"
            " + (document_id is not null)::int"
            " + (fuel_log_id is not null)::int = 1",
            name="exactly_one_owner",
        ),
        CheckConstraint("size_bytes > 0", name="positive_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(ForeignKey("garages.id", ondelete="CASCADE"), index=True)

    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True
    )
    service_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("service_events.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicle_documents.id", ondelete="CASCADE"), index=True
    )
    fuel_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("fuel_logs.id", ondelete="CASCADE"), index=True
    )

    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)

    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
