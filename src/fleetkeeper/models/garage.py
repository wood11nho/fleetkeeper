from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fleetkeeper.models.base import Base, TimestampMixin
from fleetkeeper.models.user import User


class Garage(Base, TimestampMixin):
    """A set of vehicles and the people who look after them.

    Every member sees and edits everything in the garage. There are deliberately no
    roles: in a household everyone is equal, and each extra permission level is another
    concept the least technical member of the family has to understand.
    """

    __tablename__ = "garages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))

    members: Mapped[list["GarageMember"]] = relationship(
        back_populates="garage", cascade="all, delete-orphan"
    )


class GarageMember(Base):
    __tablename__ = "garage_members"

    garage_id: Mapped[int] = mapped_column(
        ForeignKey("garages.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    garage: Mapped[Garage] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class GarageInvitation(Base, TimestampMixin):
    __tablename__ = "garage_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    garage_id: Mapped[int] = mapped_column(ForeignKey("garages.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255))
    token: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    invited_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
