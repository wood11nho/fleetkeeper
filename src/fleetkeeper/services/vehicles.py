from datetime import date

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from fleetkeeper import odometer
from fleetkeeper.inputs import IntervalInput, VehicleInput
from fleetkeeper.models.catalog import ServiceCategory
from fleetkeeper.models.enums import CategoryKind, MileageSource
from fleetkeeper.models.fuel import MileageReading
from fleetkeeper.models.garage import Garage
from fleetkeeper.models.maintenance import MaintenanceRule, ServiceEvent
from fleetkeeper.models.vehicle import Vehicle
from fleetkeeper.schedule import Reading


class OdometerWentBackwardsError(Exception):
    """A reading below the last one recorded.

    Refused rather than accepted: the average distance per day is what turns a mileage
    threshold into a warning that arrives before the deadline, and one wrong reading distorts
    it for years. A replaced instrument cluster is a real case, but it is rare enough to be
    worth handling by correcting the vehicle rather than by letting every typo through.
    """

    def __init__(self, previous_reading: int) -> None:
        self.previous_reading = previous_reading


def create(session: Session, garage: Garage, submitted: VehicleInput, author: int) -> Vehicle:
    vehicle = Vehicle(
        garage_id=garage.id,
        name=submitted.name,
        make=submitted.make,
        model=submitted.model,
        generation=submitted.generation,
        model_year=submitted.model_year,
        registration_number=submitted.registration_number,
        vin=submitted.vin,
        fuel_type=submitted.fuel_type,
        engine_code=submitted.engine_code,
        engine_displacement_cc=submitted.engine_displacement_cc,
        power_hp=submitted.power_hp,
        gearbox_type=submitted.gearbox_type,
        gearbox_gears=submitted.gearbox_gears,
        drivetrain=submitted.drivetrain,
        equipment=[item.value for item in submitted.equipment],
        first_registration_date=submitted.first_registration_date,
        current_mileage_km=submitted.current_mileage_km or 0,
        annual_mileage_km=submitted.annual_mileage_km,
        notes=submitted.notes,
        is_active=True,
    )
    session.add(vehicle)
    session.flush()

    install_rules(session, vehicle)
    if vehicle.current_mileage_km:
        _remember(
            session,
            vehicle,
            vehicle.current_mileage_km,
            on=date.today(),
            author=author,
            source=MileageSource.MANUAL,
        )

    return vehicle


def update(session: Session, vehicle: Vehicle, submitted: VehicleInput, author: int) -> None:
    """Apply an edit, then bring the schedule back in line with the car it describes."""
    vehicle.name = submitted.name
    vehicle.make = submitted.make
    vehicle.model = submitted.model
    vehicle.generation = submitted.generation
    vehicle.model_year = submitted.model_year
    vehicle.registration_number = submitted.registration_number
    vehicle.vin = submitted.vin
    vehicle.fuel_type = submitted.fuel_type
    vehicle.engine_code = submitted.engine_code
    vehicle.engine_displacement_cc = submitted.engine_displacement_cc
    vehicle.power_hp = submitted.power_hp
    vehicle.gearbox_type = submitted.gearbox_type
    vehicle.gearbox_gears = submitted.gearbox_gears
    vehicle.drivetrain = submitted.drivetrain
    vehicle.equipment = [item.value for item in submitted.equipment]
    vehicle.first_registration_date = submitted.first_registration_date
    vehicle.annual_mileage_km = submitted.annual_mileage_km
    vehicle.notes = submitted.notes

    correct_odometer(session, vehicle, submitted.current_mileage_km or 0, author=author)
    refresh_rules(session, vehicle)


def correct_odometer(session: Session, vehicle: Vehicle, corrected: int, *, author: int) -> None:
    """Set the odometer to what it should have said, rather than record a new reading.

    A correction downwards discards the readings above it, because those are the mistaken ones
    and leaving them behind would keep distorting the average distance per day — the figure
    that decides whether a warning arrives before a deadline or after it.
    """
    if corrected == vehicle.current_mileage_km:
        return

    if corrected < vehicle.current_mileage_km:
        session.execute(
            delete(MileageReading).where(
                MileageReading.vehicle_id == vehicle.id,
                MileageReading.mileage_km > corrected,
            )
        )

    vehicle.current_mileage_km = corrected
    if corrected == 0:
        return

    remaining = session.scalar(
        select(func.count())
        .select_from(MileageReading)
        .where(MileageReading.vehicle_id == vehicle.id)
    )
    if not remaining:
        _remember(
            session,
            vehicle,
            corrected,
            on=date.today(),
            author=author,
            source=MileageSource.MANUAL,
        )


def refresh_rules(session: Session, vehicle: Vehicle) -> tuple[int, int]:
    """Add rules that have become applicable and switch off those that no longer are.

    Nothing is deleted, so an interval the owner corrected and a note saying where it came from
    survive a change of mind about the gearbox. Nothing is switched back on either: a rule the
    owner turned off deliberately must stay off, and telling that apart from one this function
    turned off is not something the database records.
    """
    existing = {
        rule.category_id: rule
        for rule in session.scalars(
            select(MaintenanceRule).where(MaintenanceRule.vehicle_id == vehicle.id)
        )
    }

    added = 0
    switched_off = 0
    for category in _candidate_categories(session, vehicle):
        rule = existing.get(category.id)
        applicable = category.applies_to(vehicle)

        if applicable and rule is None:
            session.add(_rule_from(category, vehicle))
            added += 1
        elif not applicable and rule is not None and rule.is_enabled:
            rule.is_enabled = False
            switched_off += 1

    return added, switched_off


def install_rules(session: Session, vehicle: Vehicle) -> int:
    """Copy the catalogue's defaults into this vehicle's own schedule.

    From here on the intervals belong to the car: shortening the oil change on a diesel driven
    in city traffic must not touch anyone else's, and a later correction to the catalogue must
    not undo a figure the owner took from their service book.
    """
    installed = 0
    for category in _candidate_categories(session, vehicle):
        if category.applies_to(vehicle):
            session.add(_rule_from(category, vehicle))
            installed += 1
    return installed


def _candidate_categories(session: Session, vehicle: Vehicle) -> list[ServiceCategory]:
    """Catalogue entries that could give this garage a deadline.

    Documents are left out because they expire on a printed date and are tracked separately, and
    so are entries with no interval: a part replaced when it fails would otherwise produce a
    deadline nobody should act on. Both remain available for recording work that was done.
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
                or_(
                    ServiceCategory.default_interval_km.is_not(None),
                    ServiceCategory.default_interval_months.is_not(None),
                ),
            )
            .order_by(ServiceCategory.sort_order)
        )
    )


def _rule_from(category: ServiceCategory, vehicle: Vehicle) -> MaintenanceRule:
    return MaintenanceRule(
        garage_id=vehicle.garage_id,
        vehicle_id=vehicle.id,
        category_id=category.id,
        interval_km=category.default_interval_km,
        interval_months=category.default_interval_months,
        is_enabled=True,
    )


def record_odometer(
    session: Session,
    vehicle: Vehicle,
    reading: int,
    *,
    on: date,
    author: int,
    source: MileageSource = MileageSource.MANUAL,
) -> MileageReading:
    if reading < vehicle.current_mileage_km:
        raise OdometerWentBackwardsError(vehicle.current_mileage_km)

    vehicle.current_mileage_km = reading
    return _remember(session, vehicle, reading, on=on, author=author, source=source)


def _remember(
    session: Session,
    vehicle: Vehicle,
    kilometres: int,
    *,
    on: date,
    author: int,
    source: MileageSource,
) -> MileageReading:
    """Write the odometer down for one day, keeping the higher figure if that day is taken.

    A day holds one reading, enforced by the database. A second figure for the same day is
    therefore a correction of the first rather than a new fact, and the higher one wins: the
    odometer climbs through the day, so an errand after the first reading is not a contradiction.
    """
    already = session.scalar(
        select(MileageReading).where(
            MileageReading.vehicle_id == vehicle.id,
            MileageReading.recorded_on == on,
        )
    )
    if already is not None:
        if kilometres > already.mileage_km:
            already.mileage_km = kilometres
            already.source = source
        return already

    entry = MileageReading(
        garage_id=vehicle.garage_id,
        vehicle_id=vehicle.id,
        recorded_on=on,
        mileage_km=kilometres,
        source=source,
        created_by_user_id=author,
    )
    session.add(entry)
    return entry


def readings_for(session: Session, vehicle: Vehicle) -> list[Reading]:
    """Every odometer figure known for this car: one per day, in order, never decreasing.

    From both places one can be written down — readings of their own, and the mileage carried
    along by an intervention. An intervention only leaves a reading of its own when it raises the
    car's mileage, so a figure entered for a past visit would otherwise never reach the arithmetic.
    That is how the measured daily rate came out forty-four per cent below the truth on a real car.
    """
    own = session.execute(
        select(MileageReading.recorded_on, MileageReading.mileage_km).where(
            MileageReading.vehicle_id == vehicle.id
        )
    )
    with_a_service = session.execute(
        select(ServiceEvent.performed_on, ServiceEvent.mileage_km).where(
            ServiceEvent.vehicle_id == vehicle.id,
            ServiceEvent.mileage_km.is_not(None),
        )
    )

    readings = [Reading(on, kilometres) for on, kilometres in own]
    readings += [
        Reading(on, kilometres) for on, kilometres in with_a_service if kilometres is not None
    ]
    return odometer.series(readings)


def impossible_mileage(
    session: Session, vehicle: Vehicle, kilometres: int, *, on: date
) -> odometer.Bracket | None:
    """The readings that prove a figure wrong for that day, or nothing if it could be true."""
    return odometer.contradiction(readings_for(session, vehicle), on, kilometres)


def apply_interval_edits(session: Session, vehicle: Vehicle, edits: list[IntervalInput]) -> int:
    """Save an edited schedule, returning how many lines actually changed.

    Ids that do not belong to this vehicle are skipped rather than refused, so a submission from
    a stale tab cannot reach another car's schedule.
    """
    owned = {
        rule.id: rule
        for rule in session.scalars(
            select(MaintenanceRule).where(MaintenanceRule.vehicle_id == vehicle.id)
        )
    }

    changed = 0
    for edit in edits:
        rule = owned.get(edit.rule_id)
        if rule is None:
            continue

        before = (rule.interval_km, rule.interval_months, rule.is_enabled, rule.source_note)
        after = (edit.interval_km, edit.interval_months, edit.is_enabled, edit.source_note)
        if before == after:
            continue

        rule.interval_km = edit.interval_km
        rule.interval_months = edit.interval_months
        rule.is_enabled = edit.is_enabled
        rule.source_note = edit.source_note
        changed += 1

    return changed


def rules_by_section(session: Session, vehicle: Vehicle) -> list[tuple[str, list[MaintenanceRule]]]:
    """This vehicle's schedule, grouped for display in catalogue order."""
    rules = session.scalars(
        select(MaintenanceRule)
        .join(ServiceCategory, ServiceCategory.id == MaintenanceRule.category_id)
        .where(MaintenanceRule.vehicle_id == vehicle.id)
        .order_by(ServiceCategory.sort_order)
    )

    grouped: dict[str, list[MaintenanceRule]] = {}
    for rule in rules:
        grouped.setdefault(rule.category.section.value, []).append(rule)
    return list(grouped.items())
