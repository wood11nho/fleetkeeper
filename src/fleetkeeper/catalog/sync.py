from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleetkeeper.catalog.builtin import BUILTIN_CATEGORIES, CategoryDefinition
from fleetkeeper.models.catalog import ServiceCategory


@dataclass(frozen=True, slots=True)
class SyncResult:
    created: int
    updated: int
    retired: tuple[str, ...]


def sync_builtin_categories(session: Session) -> SyncResult:
    """Bring the built-in catalogue rows in line with the definitions in code.

    Safe to run as often as you like: a category is identified by its code, so correcting
    a name or an interval in code and running this again fixes the database without
    disturbing a garage's own additions, and without rewriting the per-vehicle intervals
    that were once derived from these defaults.

    Codes that exist in the database but no longer in code are reported rather than
    deleted. Service history may point at them, and a category nobody should pick again is
    a smaller problem than a delete that takes recorded work with it.
    """
    existing = {
        category.code: category
        for category in session.scalars(
            select(ServiceCategory).where(ServiceCategory.garage_id.is_(None))
        )
    }

    created = 0
    updated = 0
    for sort_order, definition in enumerate(BUILTIN_CATEGORIES):
        category = existing.get(definition.code)
        if category is None:
            session.add(ServiceCategory(code=definition.code, **_columns(definition, sort_order)))
            created += 1
        elif _apply(definition, sort_order, category):
            updated += 1

    session.flush()
    defined = {definition.code for definition in BUILTIN_CATEGORIES}
    return SyncResult(created, updated, tuple(sorted(existing.keys() - defined)))


def _columns(definition: CategoryDefinition, sort_order: int) -> dict[str, Any]:
    return {
        "name": definition.name,
        "section": definition.section,
        "kind": definition.kind,
        "default_interval_km": definition.interval_km,
        "default_interval_months": definition.interval_months,
        "interval_source": definition.source,
        "requires_fuel_types": [item.value for item in definition.fuel_types],
        "requires_gearbox_types": [item.value for item in definition.gearbox_types],
        "requires_drivetrains": [item.value for item in definition.drivetrains],
        "requires_equipment": [item.value for item in definition.equipment],
        "hint": definition.hint,
        # Display order follows the order of declaration in code, so reordering the
        # catalogue is a matter of moving a block rather than renumbering everything.
        "sort_order": sort_order,
    }


def _apply(definition: CategoryDefinition, sort_order: int, category: ServiceCategory) -> bool:
    changed = False
    for column, value in _columns(definition, sort_order).items():
        if getattr(category, column) != value:
            setattr(category, column, value)
            changed = True
    return changed
