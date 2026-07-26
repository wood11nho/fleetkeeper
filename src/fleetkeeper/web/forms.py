"""Form parsing for server-rendered pages.

FastAPI can bind a form straight to a model, but a failure then leaves the visitor looking at
a status code instead of their own half-filled form. These helpers validate by hand so a
mistake comes back as a sentence next to the field that caused it, with everything else still
typed in.
"""

from datetime import date
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
)
from pydantic_core import ErrorDetails
from starlette.datastructures import FormData

from fleetkeeper.models.enums import Drivetrain, Equipment, FuelType, GearboxType

ShortText = Annotated[str, StringConstraints(min_length=1, max_length=60)]
OptionalText = Annotated[str, StringConstraints(max_length=60)]


class VehicleForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Absent when the owner belongs to a single garage, which is the usual case; the route
    # still checks membership rather than trusting whatever arrives here.
    garage_id: int | None = None

    name: ShortText
    make: ShortText
    model: ShortText
    generation: OptionalText | None = None
    model_year: Annotated[int, Field(ge=1900)] | None = None
    registration_number: Annotated[str, StringConstraints(max_length=20)] | None = None
    vin: Annotated[str, StringConstraints(max_length=17)] | None = None

    fuel_type: FuelType
    engine_code: Annotated[str, StringConstraints(max_length=20)] | None = None
    engine_displacement_cc: Annotated[int, Field(ge=400, le=10_000)] | None = None
    power_hp: Annotated[int, Field(ge=5, le=2_000)] | None = None

    gearbox_type: GearboxType
    gearbox_gears: Annotated[int, Field(ge=3, le=12)] | None = None
    drivetrain: Drivetrain

    equipment: list[Equipment] = Field(default_factory=list)

    first_registration_date: date | None = None
    current_mileage_km: Annotated[int, Field(ge=0, le=3_000_000)] | None = None
    annual_mileage_km: Annotated[int, Field(ge=0, le=300_000)] | None = None
    notes: Annotated[str, StringConstraints(max_length=2_000)] | None = None

    @field_validator("model_year")
    @classmethod
    def not_from_the_future(cls, year: int | None) -> int | None:
        # Next year is allowed: cars are registered ahead of their model year.
        if year is not None and year > date.today().year + 1:
            raise ValueError("year is in the future")
        return year


class MileageForm(BaseModel):
    mileage_km: Annotated[int, Field(ge=0, le=3_000_000)]
    recorded_on: date | None = None


def parse[FormModel: BaseModel](
    model: type[FormModel],
    form: FormData,
    *,
    repeated: tuple[str, ...] = (),
) -> tuple[FormModel | None, dict[str, str]]:
    """Validate submitted form data, returning either the value or a message per field.

    Empty fields are dropped rather than passed along, because a browser submits an untouched
    optional box as an empty string and "" is not a number, a date, or nothing.
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
    if kind == "greater_than_equal":
        return f"Nu poate fi mai mic de {limits.get('ge')}."
    if kind == "less_than_equal":
        return f"Nu poate fi mai mare de {limits.get('le')}."
    if kind.startswith("date"):
        return "Data nu este validă."
    if kind == "enum":
        return "Alege una dintre opțiuni."
    if kind == "value_error":
        return "Anul nu poate fi în viitor."
    return "Valoarea nu este validă."


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
