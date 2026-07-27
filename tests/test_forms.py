from datetime import date, timedelta
from decimal import Decimal

from starlette.datastructures import FormData, UploadFile

from fleetkeeper.inputs import OdometerInput, ServiceEventInput, VehicleInput
from fleetkeeper.models.enums import Drivetrain, Equipment, FuelType, GearboxType
from fleetkeeper.web.forms import parse, parse_intervals, parse_parts, previous_values

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
    vehicle, errors = parse(VehicleInput, submit())

    assert errors == {}
    assert vehicle is not None
    assert vehicle.name == "Golf Plus"
    assert vehicle.equipment == []


def test_untouched_optional_boxes_do_not_become_errors() -> None:
    """A browser submits an empty box as an empty string, which is not a number or a date."""
    vehicle, errors = parse(
        VehicleInput,
        submit(("model_year", ""), ("power_hp", ""), ("first_registration_date", "")),
    )

    assert errors == {}
    assert vehicle is not None
    assert vehicle.model_year is None
    assert vehicle.power_hp is None
    assert vehicle.first_registration_date is None


def test_a_missing_required_field_is_named_in_romanian() -> None:
    incomplete = [pair for pair in COMPLETE if pair[0] != "make"]

    vehicle, errors = parse(VehicleInput, submit(base=incomplete))

    assert vehicle is None
    assert errors == {"make": "Completează acest câmp."}


def test_letters_in_a_number_are_explained_rather_than_ignored() -> None:
    vehicle, errors = parse(VehicleInput, submit(("current_mileage_km", "230.000 km")))

    assert vehicle is None
    assert "cifre" in errors["current_mileage_km"]


def test_a_year_in_the_future_is_refused() -> None:
    vehicle, errors = parse(VehicleInput, submit(("model_year", str(date.today().year + 5))))

    assert vehicle is None
    assert errors["model_year"] == "Nu poate fi în viitor."


def test_next_year_is_allowed_because_registrations_run_ahead() -> None:
    vehicle, errors = parse(VehicleInput, submit(("model_year", str(date.today().year + 1))))

    assert errors == {}
    assert vehicle is not None


def test_every_ticked_equipment_box_is_kept() -> None:
    vehicle, errors = parse(
        VehicleInput,
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
    reading, errors = parse(OdometerInput, FormData([("mileage_km", "")]))

    assert reading is None
    assert errors == {"mileage_km": "Completează acest câmp."}


def test_a_negative_odometer_reading_is_refused() -> None:
    reading, errors = parse(OdometerInput, FormData([("mileage_km", "-5")]))

    assert reading is None
    assert "mai mic" in errors["mileage_km"]


def intervention(*extra: Field) -> FormData:
    return FormData([("category_id", "1"), ("performed_on", date.today().isoformat()), *extra])


def test_an_intervention_needs_only_a_category_and_a_date() -> None:
    event, errors = parse(ServiceEventInput, intervention())

    assert errors == {}
    assert event is not None
    assert event.cost is None
    assert event.workshop is None


def test_work_cannot_have_been_done_tomorrow() -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    event, errors = parse(ServiceEventInput, intervention(("performed_on", tomorrow)))

    assert event is None
    assert errors["performed_on"] == "Nu poate fi în viitor."


def test_an_amount_written_with_a_comma_is_accepted() -> None:
    """A comma is the decimal separator here. Refusing 349,90 would be correct and useless."""
    event, errors = parse(ServiceEventInput, intervention(("cost", "349,90")))

    assert errors == {}
    assert event is not None
    assert event.cost == Decimal("349.90")


def test_an_amount_with_grouped_thousands_is_accepted() -> None:
    event, errors = parse(ServiceEventInput, intervention(("cost", "1.234,50")))

    assert errors == {}
    assert event is not None
    assert event.cost == Decimal("1234.50")


def test_a_named_part_is_kept_and_empty_rows_are_skipped() -> None:
    parts, problems = parse_parts(
        FormData(
            [
                ("part_name_0", "ulei motor"),
                ("part_brand_0", "Castrol"),
                ("part_number_0", "EDGE 5W30"),
                ("part_quantity_0", "4,5"),
                ("part_cost_0", "62,90"),
                ("part_name_1", ""),
                ("part_name_2", ""),
                ("part_name_3", ""),
            ]
        )
    )

    assert problems == {}
    assert len(parts) == 1
    assert parts[0].name == "ulei motor"
    assert parts[0].quantity == Decimal("4.50")
    assert parts[0].unit_cost == Decimal("62.90")


def test_a_part_with_no_quantity_counts_as_one() -> None:
    parts, problems = parse_parts(FormData([("part_name_0", "filtru de ulei")]))

    assert problems == {}
    assert parts[0].quantity == Decimal("1.00")


def test_a_price_with_no_part_name_is_reported() -> None:
    """Otherwise the row vanishes silently, along with the money it accounts for."""
    parts, problems = parse_parts(FormData([("part_cost_0", "62,90")]))

    assert parts == []
    assert "part_name_0" in problems


def test_a_part_priced_in_words_is_refused() -> None:
    parts, problems = parse_parts(
        FormData([("part_name_0", "ulei"), ("part_cost_0", "vreo șaizeci")])
    )

    assert parts == []
    assert "sumă" in problems["part_cost_0"]


def test_an_edited_schedule_is_read_back_per_rule() -> None:
    edits, problems = parse_intervals(
        FormData(
            [
                ("present_1", "1"),
                ("km_1", "10000"),
                ("months_1", "12"),
                ("enabled_1", "true"),
                ("note_1", "carnet service pagina 212"),
                ("present_2", "1"),
                ("km_2", ""),
                ("months_2", "24"),
                ("enabled_2", "true"),
            ]
        ),
        rule_ids={1, 2},
    )

    assert problems == {}
    assert [edit.rule_id for edit in edits] == [1, 2]
    assert edits[0].interval_km == 10_000
    assert edits[0].source_note == "carnet service pagina 212"
    assert edits[1].interval_km is None
    assert edits[1].interval_months == 24


def test_an_unticked_rule_is_switched_off_rather_than_lost() -> None:
    edits, problems = parse_intervals(
        FormData([("present_1", "1"), ("km_1", "10000"), ("months_1", "12")]), rule_ids={1}
    )

    assert problems == {}
    assert edits[0].is_enabled is False
    assert edits[0].interval_km == 10_000


def test_a_rule_the_form_never_carried_is_left_alone() -> None:
    """Otherwise a partial submission switches off every rule it failed to mention."""
    edits, problems = parse_intervals(
        FormData([("present_1", "1"), ("km_1", "10000"), ("enabled_1", "true")]),
        rule_ids={1, 2, 3},
    )

    assert problems == {}
    assert [edit.rule_id for edit in edits] == [1]


def test_a_watched_rule_with_no_interval_at_all_is_refused() -> None:
    """Watching an item with neither figure would promise a deadline that never arrives."""
    edits, problems = parse_intervals(
        FormData([("present_1", "1"), ("enabled_1", "true")]), rule_ids={1}
    )

    assert edits == []
    assert "interval" in problems["km_1"]


def test_thousands_separators_are_accepted_the_way_people_type_them() -> None:
    edits, problems = parse_intervals(
        FormData([("present_1", "1"), ("km_1", "15.000"), ("enabled_1", "true")]), rule_ids={1}
    )

    assert problems == {}
    assert edits[0].interval_km == 15_000


def test_a_zero_interval_is_refused() -> None:
    edits, problems = parse_intervals(
        FormData([("present_1", "1"), ("km_1", "0"), ("enabled_1", "true")]), rule_ids={1}
    )

    assert edits == []
    assert "mai mare de zero" in problems["km_1"]


def test_a_rule_belonging_to_another_vehicle_is_ignored() -> None:
    """A stale tab must not be able to reach a schedule it does not own."""
    edits, problems = parse_intervals(
        FormData(
            [
                ("present_1", "1"),
                ("km_1", "5000"),
                ("enabled_1", "true"),
                ("present_99", "1"),
                ("km_99", "5000"),
                ("enabled_99", "true"),
            ]
        ),
        rule_ids={1},
    )

    assert problems == {}
    assert [edit.rule_id for edit in edits] == [1]
