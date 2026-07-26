from collections import Counter

from fleetkeeper.catalog import BUILTIN_CATEGORIES
from fleetkeeper.models.catalog import ServiceCategory
from fleetkeeper.models.enums import (
    CategoryKind,
    CategorySection,
    Drivetrain,
    Equipment,
    FuelType,
    GearboxType,
)
from fleetkeeper.models.vehicle import Vehicle


def make_vehicle(
    fuel_type: FuelType = FuelType.PETROL,
    gearbox_type: GearboxType = GearboxType.MANUAL,
    drivetrain: Drivetrain = Drivetrain.FRONT,
    equipment: list[str] | None = None,
) -> Vehicle:
    return Vehicle(
        fuel_type=fuel_type,
        gearbox_type=gearbox_type,
        drivetrain=drivetrain,
        equipment=equipment if equipment is not None else [],
    )


def make_category(
    fuel_types: list[str] | None = None,
    gearbox_types: list[str] | None = None,
    drivetrains: list[str] | None = None,
    equipment: list[str] | None = None,
) -> ServiceCategory:
    return ServiceCategory(
        code="test",
        name="Test",
        section=CategorySection.OTHER,
        kind=CategoryKind.MAINTENANCE,
        requires_fuel_types=fuel_types or [],
        requires_gearbox_types=gearbox_types or [],
        requires_drivetrains=drivetrains or [],
        requires_equipment=equipment or [],
    )


def test_builtin_codes_are_unique() -> None:
    duplicates = [
        code for code, count in Counter(c.code for c in BUILTIN_CATEGORIES).items() if count > 1
    ]

    assert duplicates == []


def test_every_interval_states_where_it_came_from() -> None:
    for definition in BUILTIN_CATEGORIES:
        has_interval = definition.interval_km is not None or definition.interval_months is not None

        assert has_interval == (definition.source is not None), definition.code


def test_wear_parts_are_inspected_rather_than_scheduled() -> None:
    """A replacement interval for a brake pad is a guess dressed up as a deadline."""
    wear_parts = {
        "placute_fata",
        "placute_spate",
        "discuri_fata",
        "discuri_spate",
        "amortizoare",
        "bucse_articulatii",
        "rulmenti_roata",
        "perne_suspensie",
        "anvelope_vara",
        "anvelope_iarna",
        "baterie",
    }
    by_code = {definition.code: definition for definition in BUILTIN_CATEGORIES}

    for code in wear_parts:
        assert by_code[code].kind is CategoryKind.INSPECTION, code


def test_an_inspection_says_how_often_to_look() -> None:
    for definition in BUILTIN_CATEGORIES:
        if definition.kind is CategoryKind.INSPECTION:
            assert definition.interval_km or definition.interval_months, definition.code


def test_documents_expire_on_a_date_rather_than_an_interval() -> None:
    documents = [c for c in BUILTIN_CATEGORIES if c.kind is CategoryKind.DOCUMENT]

    assert documents
    for document in documents:
        assert document.interval_km is None
        assert document.interval_months is None


def test_category_without_requirements_applies_to_every_vehicle() -> None:
    assert make_category().applies_to(make_vehicle())


def test_spark_plugs_skip_a_diesel() -> None:
    category = make_category(fuel_types=[FuelType.PETROL])

    assert category.applies_to(make_vehicle(fuel_type=FuelType.PETROL))
    assert not category.applies_to(make_vehicle(fuel_type=FuelType.DIESEL))


def test_dual_clutch_fluid_skips_a_manual_gearbox() -> None:
    category = make_category(gearbox_types=[GearboxType.DUAL_CLUTCH_DRY])

    assert category.applies_to(make_vehicle(gearbox_type=GearboxType.DUAL_CLUTCH_DRY))
    assert not category.applies_to(make_vehicle(gearbox_type=GearboxType.MANUAL))


def test_haldex_service_needs_all_wheel_drive() -> None:
    category = make_category(drivetrains=[Drivetrain.ALL])

    assert category.applies_to(make_vehicle(drivetrain=Drivetrain.ALL))
    assert not category.applies_to(make_vehicle(drivetrain=Drivetrain.FRONT))


def test_timing_belt_service_needs_a_belt_rather_than_a_chain() -> None:
    category = make_category(equipment=[Equipment.TIMING_BELT])

    assert category.applies_to(make_vehicle(equipment=[Equipment.TIMING_BELT]))
    assert not category.applies_to(make_vehicle(equipment=[]))


def test_an_electric_car_is_never_offered_engine_work() -> None:
    combustion_only = {
        "ulei_motor",
        "filtru_aer",
        "filtru_combustibil",
        "bujii",
        "bujii_incandescente",
        "curea_accesorii",
        "curatare_egr",
        "injectoare",
        "alternator",
        "demaror",
        "sonda_lambda",
        "catalizator",
    }
    by_code = {definition.code: definition for definition in BUILTIN_CATEGORIES}

    for code in combustion_only:
        fuel_types = by_code[code].fuel_types
        assert fuel_types, f"{code} applies to every fuel type, including electric"
        assert FuelType.ELECTRIC not in fuel_types


def test_every_requirement_must_be_met_at_once() -> None:
    category = make_category(
        fuel_types=[FuelType.DIESEL],
        equipment=[Equipment.PARTICULATE_FILTER],
    )
    diesel_without_filter = make_vehicle(fuel_type=FuelType.DIESEL, equipment=[])

    assert not category.applies_to(diesel_without_filter)
