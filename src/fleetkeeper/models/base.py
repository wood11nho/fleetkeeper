from datetime import datetime
from enum import StrEnum
from typing import Annotated

from sqlalchemy import ARRAY, DateTime, Enum, MetaData, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming every constraint explicitly keeps Alembic autogenerate stable between runs and
# turns integrity errors into messages that name the rule that was broken, instead of
# referring to an identifier Postgres invented.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

StringArray = Annotated[
    list[str],
    mapped_column(ARRAY(String(40)), default=list, server_default=text("'{}'")),
]


def enum_column(enum_type: type[StrEnum]) -> Enum:
    """Store enums as their lowercase values in a checked varchar column.

    Native Postgres enum types would be tidier to read in the database, but every new
    member then needs an ALTER TYPE migration that cannot run inside a transaction.
    A varchar with a check constraint costs nothing and stays easy to extend.
    """
    return Enum(
        enum_type,
        native_enum=False,
        length=32,
        values_callable=lambda members: [member.value for member in members],
    )


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
