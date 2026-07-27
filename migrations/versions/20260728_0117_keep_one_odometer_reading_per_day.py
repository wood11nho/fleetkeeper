"""keep one odometer reading per day

Revision ID: 3b2eecef970d
Revises: d0d818a4a25c
Create Date: 2026-07-28 01:17:09.119212

Readings arrive from more than one place, so the same day could be written twice. Two figures for
one day are not two facts, and the read path already kept only the higher of them.

The delete below is what makes the constraint safe to apply to a database that has been in use:
it removes exactly the rows the constraint would reject, keeping the highest reading of each day.
Nothing else is touched, and on a database with no repeated days it changes nothing.

The downgrade drops the constraint but cannot bring those rows back. They were duplicates that no
calculation ever used, so there is nothing there to restore.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3b2eecef970d"
down_revision: str | Sequence[str] | None = "d0d818a4a25c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DISCARD_REPEATED_DAYS = sa.text("""
    delete from mileage_readings
    where id in (
        select id
        from (
            select
                id,
                row_number() over (
                    partition by vehicle_id, recorded_on
                    order by mileage_km desc, id
                ) as ordinal
            from mileage_readings
        ) ranked
        where ranked.ordinal > 1
    )
""")


def upgrade() -> None:
    op.execute(DISCARD_REPEATED_DAYS)
    op.create_unique_constraint(
        op.f("uq_mileage_readings_vehicle_id_recorded_on"),
        "mileage_readings",
        ["vehicle_id", "recorded_on"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_mileage_readings_vehicle_id_recorded_on"),
        "mileage_readings",
        type_="unique",
    )
