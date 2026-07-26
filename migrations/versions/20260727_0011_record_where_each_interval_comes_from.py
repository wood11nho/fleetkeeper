"""record where each interval comes from

Revision ID: e0facea9e594
Revises: 9c137cce3da6
Create Date: 2026-07-27 00:11:51.135753

Autogenerate found the new column and, as always, missed the check constraint, since it
does not compare those. The constraint is written out below by hand.

The built-in catalogue rows are deleted rather than backfilled. They are a projection of
`catalog/builtin.py` rather than anything a user typed, `fleetkeeper sync-catalog` puts them
back with their sources attached, and a migration has no business importing application
code to work out what each source should be. A garage's own categories are left alone, and
the delete fails loudly instead of cascading if a service event ever references a built-in
category by then.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e0facea9e594"
down_revision: str | Sequence[str] | None = "9c137cce3da6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INTERVAL_NEEDS_A_SOURCE = (
    "(default_interval_km is null and default_interval_months is null) = (interval_source is null)"
)


def upgrade() -> None:
    op.add_column(
        "service_categories",
        sa.Column(
            "interval_source",
            sa.Enum(
                "manufacturer",
                "practice",
                "estimate",
                name="intervalsource",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
    )
    op.execute("delete from service_categories where garage_id is null")
    op.create_check_constraint(
        "interval_needs_a_source", "service_categories", INTERVAL_NEEDS_A_SOURCE
    )


def downgrade() -> None:
    # The bare name, not the prefixed one: the metadata naming convention expands it, and
    # passing the full name gets it prefixed a second time and truncated.
    op.drop_constraint("interval_needs_a_source", "service_categories", type_="check")
    op.execute("delete from service_categories where garage_id is null")
    op.drop_column("service_categories", "interval_source")
