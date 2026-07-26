from datetime import date

from starlette.datastructures import FormData, UploadFile

from fleetkeeper.models.enums import Drivetrain, Equipment, FuelType, GearboxType
from fleetkeeper.web.forms import MileageForm, VehicleForm, parse, previous_values

# FormData accepts uploads alongside text, so the pairs have to be typed as widely as it does.
Field = tuple[str, str | UploadFile]

COMPLETE: list[Field] = [
    ("name", "Golf Plus"),
    ("make", "Volkswagen"),
    ("model", "Golf Plus"),
    ("fuel_type", FuelType.DIESEL.value),
    ("gearbox_type", GearboxType.MANUAL.value),
    ("drivetrain", Drivetrain.FRONT.value),
]


def submit(*extra: Field, base: list[Field] | None = None) -> FormData:
    return FormData((base if base is not None else COMPLETE) + list(extra))


def test_the_minimum_a_vehicle_needs_is_accepted() -> None:
    vehicle, errors = parse(VehicleForm, submit())

    assert errors == {}
    assert vehicle is not None
    assert vehicle.name == "Golf Plus"
    assert vehicle.equipment == []


def test_untouched_optional_boxes_do_not_become_errors() -> None:
    """A browser submits an empty box as an empty string, which is not a number or a date."""
    vehicle, errors = parse(
        VehicleForm,
        submit(("model_year", ""), ("power_hp", ""), ("first_registration_date", "")),
    )

    assert errors == {}
    assert vehicle is not None
    assert vehicle.model_year is None
    assert vehicle.power_hp is None
    assert vehicle.first_registration_date is None


def test_a_missing_required_field_is_named_in_romanian() -> None:
    incomplete = [pair for pair in COMPLETE if pair[0] != "make"]

    vehicle, errors = parse(VehicleForm, submit(base=incomplete))

    assert vehicle is None
    assert errors == {"make": "Completează acest câmp."}


def test_letters_in_a_number_are_explained_rather_than_ignored() -> None:
    vehicle, errors = parse(VehicleForm, submit(("current_mileage_km", "230.000 km")))

    assert vehicle is None
    assert "cifre" in errors["current_mileage_km"]


def test_a_year_in_the_future_is_refused() -> None:
    vehicle, errors = parse(VehicleForm, submit(("model_year", str(date.today().year + 5))))

    assert vehicle is None
    assert errors["model_year"] == "Anul nu poate fi în viitor."


def test_next_year_is_allowed_because_registrations_run_ahead() -> None:
    vehicle, errors = parse(VehicleForm, submit(("model_year", str(date.today().year + 1))))

    assert errors == {}
    assert vehicle is not None


def test_every_ticked_equipment_box_is_kept() -> None:
    vehicle, errors = parse(
        VehicleForm,
        submit(
            ("equipment", Equipment.TIMING_BELT.value),
            ("equipment", Equipment.AIR_CONDITIONING.value),
        ),
        repeated=("equipment",),
    )

    assert errors == {}
    assert vehicle is not None
    assert vehicle.equipment == [Equipment.TIMING_BELT, Equipment.AIR_CONDITIONING]


def test_a_rejected_form_comes_back_with_all_its_ticks() -> None:
    """Reading repeated fields as single values silently drops all but the last tick."""
    form = submit(
        ("equipment", Equipment.TIMING_BELT.value),
        ("equipment", Equipment.AIR_CONDITIONING.value),
    )

    kept = previous_values(form, repeated=("equipment",))

    assert kept["equipment"] == [Equipment.TIMING_BELT.value, Equipment.AIR_CONDITIONING.value]
    assert kept["name"] == "Golf Plus"


def test_an_odometer_reading_needs_a_number() -> None:
    reading, errors = parse(MileageForm, FormData([("mileage_km", "")]))

    assert reading is None
    assert errors == {"mileage_km": "Completează acest câmp."}


def test_a_negative_odometer_reading_is_refused() -> None:
    reading, errors = parse(MileageForm, FormData([("mileage_km", "-5")]))

    assert reading is None
    assert "mai mic" in errors["mileage_km"]
