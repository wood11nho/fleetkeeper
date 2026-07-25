from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from fleetkeeper.models.base import Base, enum_column
from fleetkeeper.models.enums import JobStatus, NotificationStatus


class NotificationLog(Base):
    """Every reminder the application tried to send.

    reminder_key identifies one deadline at one warning threshold, which is what stops a
    reminder being resent every morning until the work is done. It doubles as the record
    the administration screen reads when the question is whether yesterday's mail left.
    """

    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int | None] = mapped_column(ForeignKey("garages.id", ondelete="SET NULL"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    recipient: Mapped[str] = mapped_column(String(255))
    reminder_key: Mapped[str] = mapped_column(String(200), unique=True)
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[NotificationStatus] = mapped_column(enum_column(NotificationStatus))
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class JobRun(Base):
    """One execution of a scheduled job, so a silent failure is still visible."""

    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_name: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[JobStatus] = mapped_column(enum_column(JobStatus))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items_processed: Mapped[int | None]
    notifications_sent: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)
