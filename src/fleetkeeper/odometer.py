"""Reading the odometer history: how fast a car covers ground, and what the odometer said on a
day nobody wrote it down.

Like `schedule`, deliberately free of any database access. It produces the values `schedule`
consumes, and both can be tested exhaustively without a single row anywhere.

Two jobs. The first is a daily rate, because a mileage threshold only becomes a date once you
know how far the car travels. The second is filling in the odometer for a day with no reading:
an intervention recorded from memory often has no mileage on it, and without one, a threshold
measured in kilometres has nothing to count from.

Everything inferred is labelled with how firm it is. A figure read off the dashboard, a figure
bracketed by two real readings, and a figure projected past the end of the history are three
different claims, and showing them identically invites trust the weakest one has not earned.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from fleetkeeper.schedule import DailyDistance, DistanceBasis, Reading, add_months

# Long enough to average out a winter, short enough that a commute given up years ago stops
# counting. A car's habits change with its owner's, and the recent past describes it better.
MEASUREMENT_WINDOW_MONTHS = 24

# Three points are the fewest that can show a trend rather than just a pair of ends.
TREND_MINIMUM_READINGS = 3

# Two readings a week apart extrapolate to nonsense.
MINIMUM_SPAN_DAYS = 30

DAYS_PER_YEAR = 365.25


class MileageBasis(StrEnum):
    """How firm a mileage figure for one particular day is."""

    # Somebody read it off the dashboard and wrote it down.
    RECORDED = "recorded"

    # Between two real readings. The odometer only goes up, so the true figure is certainly
    # between them and the error is bounded by how much the rate varied in between.
    INTERPOLATED = "interpolated"

    # Outside the readings, worked out from the daily rate. Nothing bounds this one, and the
    # further out it reaches the weaker it gets.
    PROJECTED = "projected"

    NONE = "none"


@dataclass(frozen=True, slots=True)
class Estimate:
    kilometres: int | None
    basis: MileageBasis

    @property
    def is_recorded(self) -> bool:
        return self.basis is MileageBasis.RECORDED


@dataclass(frozen=True, slots=True)
class Pace:
    """A daily rate together with what backs it, so the interface can qualify what it shows."""

    distance: DailyDistance
    readings_used: int
    span_days: int


def series(readings: Iterable[Reading]) -> list[Reading]:
    """Put a pile of readings in order: one per day, ascending, never decreasing.

    Readings arrive from more than one place — entered on their own, and carried along by an
    intervention — so the same day can turn up twice. The higher figure wins, since the odometer
    only goes up and the lower one was read earlier in the day.

    A reading below one from an earlier date is dropped rather than kept. It cannot be true, so
    it is a typing mistake, and leaving it in would produce a negative rate.
    """
    highest_on_day: dict[date, int] = {}
    for reading in readings:
        known = highest_on_day.get(reading.on)
        if known is None or reading.kilometres > known:
            highest_on_day[reading.on] = reading.kilometres

    ordered: list[Reading] = []
    highest = -1
    for on in sorted(highest_on_day):
        kilometres = highest_on_day[on]
        if kilometres < highest:
            continue
        highest = kilometres
        ordered.append(Reading(on, kilometres))
    return ordered


def pace(
    readings: Iterable[Reading],
    *,
    today: date,
    annual_estimate: int | None = None,
) -> Pace:
    """How far this car covers in a day.

    Preferring, in order: a trend fitted through the readings of the last two years, the same
    trend fitted through the whole history, the straight line between the two readings furthest
    apart, and finally the figure the owner gave when adding the car.

    A trend rather than the two end readings once there are three of them, because with only the
    ends, one mistyped digit at either end moves the entire answer. Least squares lets every
    reading pull a little, so a single odd one bends the line instead of defining it.
    """
    ordered = series(readings)
    window_start = add_months(today, -MEASUREMENT_WINDOW_MONTHS)
    recent = [reading for reading in ordered if reading.on >= window_start]

    for candidate in (recent, ordered):
        if len(candidate) >= TREND_MINIMUM_READINGS:
            measured = _trend(candidate)
            if measured is not None:
                return measured

    measured = _between_ends(ordered)
    if measured is not None:
        return measured

    if annual_estimate and annual_estimate > 0:
        estimated = DailyDistance(annual_estimate / DAYS_PER_YEAR, DistanceBasis.ESTIMATED)
        return Pace(estimated, len(ordered), _span(ordered))

    return Pace(DailyDistance(None, DistanceBasis.NONE), len(ordered), _span(ordered))


def kilometres_on(
    readings: list[Reading],
    when: date,
    rate: Pace,
    *,
    began: date | None = None,
) -> Estimate:
    """What the odometer read on a given day, as well as can be told.

    `readings` is expected to have been through `series` already.

    `began` is the earliest day this car could have shown zero kilometres — its first
    registration, or failing that the start of the year it was built. It is used as a floor and
    not as a second reading: for a car bought second hand, the date in the papers may be a later
    registration rather than the day it left the factory, so it is a bound worth trusting and a
    figure that is not.
    """
    if not readings:
        return Estimate(None, MileageBasis.NONE)

    for reading in readings:
        if reading.on == when:
            return Estimate(reading.kilometres, MileageBasis.RECORDED)

    first, last = readings[0], readings[-1]
    if first.on < when < last.on:
        return Estimate(_interpolated(readings, when), MileageBasis.INTERPOLATED)

    per_day = rate.distance.per_day
    if per_day is None:
        return Estimate(None, MileageBasis.NONE)

    if when > last.on:
        ahead = round(per_day * (when - last.on).days)
        return Estimate(last.kilometres + ahead, MileageBasis.PROJECTED)

    if began is not None and when < began:
        # The car did not exist yet, so there is no figure to give rather than a small one.
        return Estimate(None, MileageBasis.NONE)

    behind = round(per_day * (first.on - when).days)
    return Estimate(max(0, first.kilometres - behind), MileageBasis.PROJECTED)


def _interpolated(readings: list[Reading], when: date) -> int:
    before = [reading for reading in readings if reading.on < when][-1]
    after = next(reading for reading in readings if reading.on > when)

    span = (after.on - before.on).days
    travelled = after.kilometres - before.kilometres
    return before.kilometres + round(travelled * (when - before.on).days / span)


def _trend(readings: list[Reading]) -> Pace | None:
    """The least squares slope through the readings, in kilometres a day."""
    span = _span(readings)
    if span < MINIMUM_SPAN_DAYS:
        return None

    origin = readings[0].on
    days = [(reading.on - origin).days for reading in readings]
    mean_day = sum(days) / len(days)
    mean_kilometres = sum(reading.kilometres for reading in readings) / len(readings)

    spread = sum((day - mean_day) ** 2 for day in days)
    if spread == 0:
        return None

    together = sum(
        (day - mean_day) * (reading.kilometres - mean_kilometres)
        for day, reading in zip(days, readings, strict=True)
    )
    slope = together / spread
    if slope <= 0:
        # A car that has not moved does not travel zero kilometres a day for ever.
        return None

    return Pace(DailyDistance(slope, DistanceBasis.MEASURED), len(readings), span)


def _between_ends(readings: list[Reading]) -> Pace | None:
    if len(readings) < 2:
        return None

    span = _span(readings)
    travelled = readings[-1].kilometres - readings[0].kilometres
    if span < MINIMUM_SPAN_DAYS or travelled <= 0:
        return None

    return Pace(DailyDistance(travelled / span, DistanceBasis.MEASURED), len(readings), span)


def _span(readings: list[Reading]) -> int:
    if len(readings) < 2:
        return 0
    return (readings[-1].on - readings[0].on).days
