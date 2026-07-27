from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from fleetkeeper.inputs import PartInput, ServiceEventInput
from fleetkeeper.models.catalog import ServiceCategory
from fleetkeeper.models.enums import CategoryKind, MileageSource
from fleetkeeper.models.maintenance import ServiceEvent, ServiceEventItem
from fleetkeeper.models.vehicle import Vehicle
from fleetkeeper.services import vehicles


@dataclass(frozen=True, slots=True)
class Suggestions:
    """What this garage has typed before, offered back as autocomplete.

    Gathered from the garage's own history rather than from a list written in advance: there are
    tens of thousands of parts, any list would be out of date the day after it was written, and
    the entries that matter are the ones these cars actually use.
    """

    workshops: list[str]
    part_names: list[str]
    brands: list[str]


def record(
    session: Session,
    vehicle: Vehicle,
    submitted: ServiceEventInput,
    parts: list[PartInput],
    author: int,
) -> ServiceEvent:
    """Write down work that was done, and take the odometer reading that came with it.

    Someone recording an oil change has just read the odometer, so asking again on another screen
    would be asking twice. A reading lower than what is already known is ignored rather than
    refused: the mileage is a detail of the record here, and losing the whole intervention over it
    would be a poor trade.
    """
    event = ServiceEvent(
        garage_id=vehicle.garage_id,
        vehicle_id=vehicle.id,
        category_id=submitted.category_id,
        performed_on=submitted.performed_on,
        mileage_km=submitted.mileage_km,
        cost=submitted.cost,
        workshop=submitted.workshop,
        notes=submitted.notes,
        created_by_user_id=author,
    )
    session.add(event)
    session.flush()

    for part in parts:
        session.add(
            ServiceEventItem(
                service_event_id=event.id,
                name=part.name,
                brand=part.brand,
                part_number=part.part_number,
                quantity=part.quantity,
                unit_cost=part.unit_cost,
            )
        )

    if submitted.mileage_km and submitted.mileage_km > vehicle.current_mileage_km:
        vehicles.record_odometer(
            session,
            vehicle,
            submitted.mileage_km,
            on=submitted.performed_on,
            author=author,
            source=MileageSource.SERVICE_EVENT,
        )

    return event


def remove(session: Session, event: ServiceEvent) -> None:
    """Delete an intervention and its parts.

    The odometer reading it produced is left behind on purpose. It was a real reading on a real
    day, and removing a mistyped category should not quietly rewrite the mileage history.
    """
    session.delete(event)


def for_vehicle(
    session: Session,
    vehicle: Vehicle,
    *,
    category_id: int | None = None,
    year: int | None = None,
) -> list[ServiceEvent]:
    query = (
        select(ServiceEvent)
        .options(selectinload(ServiceEvent.items), selectinload(ServiceEvent.category))
        .where(ServiceEvent.vehicle_id == vehicle.id)
        .order_by(ServiceEvent.performed_on.desc(), ServiceEvent.id.desc())
    )
    if category_id is not None:
        query = query.where(ServiceEvent.category_id == category_id)
    if year is not None:
        query = query.where(func.extract("year", ServiceEvent.performed_on) == year)

    return list(session.scalars(query))


def recorded_years(session: Session, vehicle: Vehicle) -> list[int]:
    # SELECT DISTINCT on the statement rather than a distinct() call around the expression: the
    # latter also lands in the ORDER BY, where it is not valid SQL.
    year = func.extract("year", ServiceEvent.performed_on)
    years = session.scalars(
        select(year).where(ServiceEvent.vehicle_id == vehicle.id).distinct().order_by(year.desc())
    )
    return [int(value) for value in years]


def total_spent(session: Session, vehicle: Vehicle) -> tuple[int, Decimal]:
    """How many interventions are on record and what they add up to.

    Money stays a Decimal all the way through. Adding up prices as floating point is how a total
    ends up two bani short of the invoices it came from.
    """
    counted, summed = session.execute(
        select(func.count(ServiceEvent.id), func.coalesce(func.sum(ServiceEvent.cost), 0)).where(
            ServiceEvent.vehicle_id == vehicle.id
        )
    ).one()
    return int(counted), Decimal(summed)


def loggable_categories(session: Session, vehicle: Vehicle) -> list[ServiceCategory]:
    """Everything that can be recorded as work done.

    Wider than the vehicle's schedule on purpose. A clutch or a particulate filter has no interval
    and so never produces a deadline, but it certainly gets replaced, and an item switched off
    still needs somewhere to be written down when it happens anyway.
    """
    return list(
        session.scalars(
            select(ServiceCategory)
            .where(
                ServiceCategory.kind != CategoryKind.DOCUMENT,
                or_(
                    ServiceCategory.garage_id.is_(None),
                    ServiceCategory.garage_id == vehicle.garage_id,
                ),
            )
            .order_by(ServiceCategory.sort_order)
        )
    )


def suggestions(session: Session, garage_id: int) -> Suggestions:
    of_this_garage = ServiceEvent.garage_id == garage_id
    items_of_this_garage = ServiceEventItem.service_event_id.in_(
        select(ServiceEvent.id).where(of_this_garage)
    )

    return Suggestions(
        workshops=_texts(
            session.scalars(select(ServiceEvent.workshop).where(of_this_garage).distinct())
        ),
        part_names=_texts(
            session.scalars(select(ServiceEventItem.name).where(items_of_this_garage).distinct())
        ),
        brands=_texts(
            session.scalars(select(ServiceEventItem.brand).where(items_of_this_garage).distinct())
        ),
    )


def latest(session: Session, vehicle: Vehicle, limit: int) -> list[ServiceEvent]:
    return list(
        session.scalars(
            select(ServiceEvent)
            .options(selectinload(ServiceEvent.category))
            .where(ServiceEvent.vehicle_id == vehicle.id)
            .order_by(ServiceEvent.performed_on.desc(), ServiceEvent.id.desc())
            .limit(limit)
        )
    )


def last_done(session: Session, vehicle: Vehicle) -> dict[int, date]:
    """The most recent date each category was recorded, keyed by category.

    The due-date engine will need exactly this, and the history page uses it to show how long ago
    something was last seen to.
    """
    rows = session.execute(
        select(ServiceEvent.category_id, func.max(ServiceEvent.performed_on))
        .where(ServiceEvent.vehicle_id == vehicle.id)
        .group_by(ServiceEvent.category_id)
    )
    return {category_id: performed_on for category_id, performed_on in rows}


def _texts(values: Iterable[str | None]) -> list[str]:
    found = {value.strip() for value in values if value and value.strip()}
    return sorted(found, key=str.casefold)
