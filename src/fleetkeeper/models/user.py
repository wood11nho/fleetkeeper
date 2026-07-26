from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from fleetkeeper.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))

    # Granted by hand in the database. There is exactly one platform administrator and
    # no reason to build a screen for promoting a second one.
    is_platform_admin: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # The application is reachable from the open internet with two accounts on it, so a
    # password guessing attempt would otherwise be limited only by network speed.
    failed_login_count: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
