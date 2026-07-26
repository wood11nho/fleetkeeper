"""Validated input, once it has stopped being an HTTP form and before it becomes a row.

Kept out of the web package so that the domain services can accept it without depending on
anything to do with requests, and out of the models package so that a rejected value never
reaches the database. The plumbing that turns a submitted form into one of these lives in
web/forms.py.
"""

from dataclasses import dataclass
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from fleetkeeper.models.enums import Drivetrain, Equipment, FuelType, GearboxType

ShortText = Annotated[str, StringConstraints(min_length=1, max_length=60)]
OptionalText = Annotated[str, StringConstraints(max_length=60)]


class VehicleInput(BaseModel):
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


class OdometerInput(BaseModel):
    mileage_km: Annotated[int, Field(ge=0, le=3_000_000)]
    recorded_on: date | None = None


@dataclass(frozen=True, slots=True)
class IntervalInput:
    """One line of a vehicle's schedule as the owner has just edited it."""

    rule_id: int
    interval_km: int | None
    interval_months: int | None
    is_enabled: bool
    source_note: str | None
