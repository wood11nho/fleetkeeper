from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fleetkeeper.models.base import Base
from fleetkeeper.models.user import User


class UserSession(Base):
    """A signed-in browser.

    Sessions live in the database rather than inside a signed cookie so that they can be
    ended from the server: a phone left in a taxi is a realistic problem, and a cookie that
    is valid for thirty days cannot be taken back.

    Only the digest of the token is stored. A leaked backup then reveals nothing that can be
    used to sign in.
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Enough to recognise which device this is when reviewing sessions, and no more.
    user_agent: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship()
