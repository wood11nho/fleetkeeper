from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fleetkeeper.models.catalog import ServiceCategory
from fleetkeeper.models.enums import CategoryKind, MileageSource
from fleetkeeper.models.fuel import MileageReading
from fleetkeeper.models.garage import Garage
from fleetkeeper.models.maintenance import MaintenanceRule
from fleetkeeper.models.vehicle import Vehicle
from fleetkeeper.web.forms import VehicleForm


class OdometerWentBackwardsError(Exception):
    """A reading below the last one recorded.

    Refused rather than accepted: the average distance per day is what turns a mileage
    threshold into a warning that arrives before the deadline, and one wrong reading distorts
    it for years. A replaced instrument cluster is a real case, but it is rare enough to be
    worth handling by correcting the vehicle rather than by letting every typo through.
    """

    def __init__(self, previous_reading: int) -> None:
        self.previous_reading = previous_reading


def create(session: Session, garage: Garage, submitted: VehicleForm, author: int) -> Vehicle:
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
        session.add(
            MileageReading(
                garage_id=vehicle.garage_id,
                vehicle_id=vehicle.id,
                recorded_on=date.today(),
                mileage_km=vehicle.current_mileage_km,
                source=MileageSource.MANUAL,
                created_by_user_id=author,
            )
        )

    return vehicle


def install_rules(session: Session, vehicle: Vehicle) -> int:
    """Copy the catalogue's defaults into this vehicle's own schedule.

    From here on the intervals belong to the car: shortening the oil change on a diesel driven
    in city traffic must not touch anyone else's, and a later correction to the catalogue must
    not undo a figure the owner took from their service book.

    Only items with an interval get a rule. Documents expire on a printed date, and a part that
    is replaced when it fails would produce a deadline nobody should act on.
    """
    applicable = session.scalars(
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

    installed = 0
    for category in applicable:
        if category.default_interval_km is None and category.default_interval_months is None:
            continue
        if not category.applies_to(vehicle):
            continue

        session.add(
            MaintenanceRule(
                garage_id=vehicle.garage_id,
                vehicle_id=vehicle.id,
                category_id=category.id,
                interval_km=category.default_interval_km,
                interval_months=category.default_interval_months,
                is_enabled=True,
            )
        )
        installed += 1

    return installed


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
    entry = MileageReading(
        garage_id=vehicle.garage_id,
        vehicle_id=vehicle.id,
        recorded_on=on,
        mileage_km=reading,
        source=source,
        created_by_user_id=author,
    )
    session.add(entry)
    return entry


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
