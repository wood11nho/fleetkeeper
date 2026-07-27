"""Turning submitted forms into validated input, or into sentences a person can act on.

FastAPI can bind a form straight to a model, but a failure then leaves the visitor looking at
a status code instead of their own half-filled form. These helpers validate by hand so a
mistake comes back beside the field that caused it, with everything else still typed in.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails
from starlette.datastructures import FormData

from fleetkeeper.inputs import IntervalInput, PartInput, as_decimal_text

NOTE_LIMIT = 200


def parse[Model: BaseModel](
    model: type[Model],
    form: FormData,
    *,
    repeated: tuple[str, ...] = (),
) -> tuple[Model | None, dict[str, str]]:
    """Validate submitted form data, returning either the value or a message per field.

    Empty fields are dropped rather than passed along, because a browser submits an untouched
    optional box as an empty string, and "" is not a number, a date, or nothing.
    """
    submitted: dict[str, Any] = {}
    for key in set(form.keys()):
        if key in repeated:
            submitted[key] = form.getlist(key)
            continue
        value = form.get(key)
        if isinstance(value, str) and value.strip():
            submitted[key] = value

    try:
        return model.model_validate(submitted), {}
    except ValidationError as invalid:
        return None, _explain(invalid)


PRESENT_PREFIX = "present_"


def parse_intervals(
    form: FormData, rule_ids: set[int]
) -> tuple[list[IntervalInput], dict[str, str]]:
    """Read the schedule editing form, which has one row of fields per rule.

    Only rules the form actually carried are touched, marked by a hidden field per row. An
    unticked box and an absent row look identical otherwise, so a partial submission would
    switch off every rule it failed to mention.

    Ids the vehicle does not own are skipped rather than refused: a stale tab is a normal thing
    to submit, and either way it must not reach another car's schedule.
    """
    edits: list[IntervalInput] = []
    problems: dict[str, str] = {}

    for rule_id in sorted(rule_ids):
        if form.get(f"{PRESENT_PREFIX}{rule_id}") is None:
            continue

        enabled = form.get(f"enabled_{rule_id}") is not None
        kilometres, kilometre_problem = _optional_count(form.get(f"km_{rule_id}"))
        months, month_problem = _optional_count(form.get(f"months_{rule_id}"))
        note = str(form.get(f"note_{rule_id}") or "").strip() or None

        if kilometre_problem:
            problems[f"km_{rule_id}"] = kilometre_problem
        if month_problem:
            problems[f"months_{rule_id}"] = month_problem
        if note and len(note) > NOTE_LIMIT:
            problems[f"note_{rule_id}"] = f"Cel mult {NOTE_LIMIT} de caractere."
        if enabled and kilometres is None and months is None and not kilometre_problem:
            problems[f"km_{rule_id}"] = (
                "Pune un interval, în kilometri sau în luni, ori stinge operațiunea."
            )

        edits.append(
            IntervalInput(
                rule_id=rule_id,
                interval_km=kilometres,
                interval_months=months,
                is_enabled=enabled,
                source_note=note,
            )
        )

    return ([] if problems else edits), problems


PART_ROWS = 4


def parse_parts(form: FormData) -> tuple[list[PartInput], dict[str, str]]:
    """Read the part rows, keeping only those that were given a name.

    Empty rows are how the form offers room for more parts than most jobs need, so they are
    skipped rather than reported. A row with a price but no name is a mistake worth naming,
    though: it would otherwise vanish along with the money it accounts for.
    """
    parts: list[PartInput] = []
    problems: dict[str, str] = {}

    for row in range(PART_ROWS):
        name = str(form.get(f"part_name_{row}") or "").strip()
        quantity_raw = str(form.get(f"part_quantity_{row}") or "").strip()
        cost_raw = str(form.get(f"part_cost_{row}") or "").strip()

        if not name:
            if quantity_raw or cost_raw:
                problems[f"part_name_{row}"] = "Scrie ce piesă este, sau lasă rândul complet gol."
            continue

        quantity, quantity_problem = _amount(quantity_raw or "1")
        unit_cost, cost_problem = _amount(cost_raw)

        if quantity_problem or quantity is None or quantity <= 0:
            problems[f"part_quantity_{row}"] = (
                quantity_problem or "Trebuie să fie mai mare de zero."
            )
            continue
        if cost_problem:
            problems[f"part_cost_{row}"] = cost_problem
            continue

        parts.append(
            PartInput(
                name=name[:120],
                brand=(str(form.get(f"part_brand_{row}") or "").strip() or None),
                part_number=(str(form.get(f"part_number_{row}") or "").strip() or None),
                quantity=quantity,
                unit_cost=unit_cost,
            )
        )

    return ([] if problems else parts), problems


def previous_values(form: FormData, *, repeated: tuple[str, ...] = ()) -> dict[str, Any]:
    """What the visitor typed, so a rejected form comes back filled in rather than blank.

    Repeated fields have to be read as lists; reading a set of ticked boxes as a single value
    keeps only the last one, and the visitor gets their form back with most of their ticks
    quietly removed.
    """
    kept: dict[str, Any] = {}
    for key in set(form.keys()):
        if key in repeated:
            kept[key] = form.getlist(key)
            continue
        value = form.get(key)
        if isinstance(value, str):
            kept[key] = value
    return kept


def _amount(raw: Any) -> tuple[Decimal | None, str | None]:
    text = as_decimal_text(str(raw or ""))
    if not text:
        return None, None
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None, "Scrie o sumă, de exemplu 350 sau 349,90."
    if value < 0:
        return None, "Suma nu poate fi negativă."
    return value.quantize(Decimal("0.01")), None


def _optional_count(raw: Any) -> tuple[int | None, str | None]:
    text = str(raw or "").strip().replace(".", "").replace(" ", "")
    if not text:
        return None, None
    if not text.isdigit():
        return None, "Scrie doar cifre, fără litere."
    value = int(text)
    if value <= 0:
        return None, "Trebuie să fie mai mare de zero."
    return value, None


def _explain(invalid: ValidationError) -> dict[str, str]:
    explained: dict[str, str] = {}
    for problem in invalid.errors():
        field = str(problem["loc"][0]) if problem["loc"] else "form"
        explained.setdefault(field, _sentence(problem))
    return explained


def _sentence(problem: ErrorDetails) -> str:
    kind = problem["type"]
    limits = problem.get("ctx") or {}

    if kind in {"missing", "string_too_short"}:
        return "Completează acest câmp."
    if kind == "string_too_long":
        return f"Cel mult {limits.get('max_length')} de caractere."
    if kind in {"int_parsing", "int_type"}:
        return "Scrie doar cifre, fără spații, puncte sau litere."
    if kind.startswith("decimal"):
        return "Scrie o sumă, de exemplu 350 sau 349,90."
    if kind == "greater_than":
        return f"Trebuie să fie mai mare de {limits.get('gt')}."
    if kind == "greater_than_equal":
        return f"Nu poate fi mai mic de {limits.get('ge')}."
    if kind == "less_than_equal":
        return f"Nu poate fi mai mare de {limits.get('le')}."
    if kind.startswith("date"):
        return "Data nu este validă."
    if kind == "enum":
        return "Alege una dintre opțiuni."
    # The only rules that raise a plain value error are the two that refuse the future: a model
    # year and the date work was done.
    if kind == "value_error":
        return "Nu poate fi în viitor."
    return "Valoarea nu este validă."
