"""Working out when something falls due.

Deliberately free of any database access. Everything this needs arrives as plain values, which
means the rules can be tested exhaustively without a single row anywhere, and the reasoning stays
readable rather than being spread across queries.

The shape of a real service schedule is *every 15,000 km or 12 months, whichever comes sooner*.
Two intervals, and the earlier one wins. The awkward part is that one of them is a distance and
the other is a date, and a reminder has to arrive on a day — so a distance has to be turned into
a date, using how far this car actually travels.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

# A reminder is worth having only if it arrives with time to book an appointment.
DEFAULT_WARNING_DAYS = 30
DEFAULT_WARNING_KILOMETRES = 1_000

# Two readings a week apart extrapolate to nonsense. Below this span the measured rate is thrown
# away in favour of the owner's own estimate, which is at least a considered figure.
MINIMUM_MEASURED_SPAN_DAYS = 30

DAYS_PER_YEAR = 365.25


class DueStatus(StrEnum):
    OVERDUE = "overdue"
    SOON = "soon"
    OK = "ok"

    # Nothing of this kind has ever been recorded, so there is no last time to count from. Not a
    # problem with the car — a gap in the history, and the only honest thing to do is say so.
    UNKNOWN = "unknown"


class DistanceBasis(StrEnum):
    """Where the daily distance came from, so the interface can say how firm the date is."""

    MEASURED = "measured"
    ESTIMATED = "estimated"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class Reading:
    on: date
    kilometres: int


@dataclass(frozen=True, slots=True)
class Interval:
    kilometres: int | None
    months: int | None

    @property
    def exists(self) -> bool:
        return self.kilometres is not None or self.months is not None


@dataclass(frozen=True, slots=True)
class LastDone:
    on: date
    kilometres: int | None


@dataclass(frozen=True, slots=True)
class Thresholds:
    days: int = DEFAULT_WARNING_DAYS
    kilometres: int = DEFAULT_WARNING_KILOMETRES


@dataclass(frozen=True, slots=True)
class DailyDistance:
    per_day: float | None
    basis: DistanceBasis

    def days_to_cover(self, kilometres: int) -> int | None:
        if self.per_day is None or self.per_day <= 0:
            return None
        return max(0, round(kilometres / self.per_day))


@dataclass(frozen=True, slots=True)
class Due:
    """When one item on one car falls due, and how sure we are of it."""

    status: DueStatus
    last_done: LastDone | None

    due_on: date | None
    """From the interval in months, counted from the last time it was done."""

    due_at_km: int | None
    """From the interval in kilometres, counted from the mileage it was last done at."""

    projected_on: date | None
    """The day the odometer is expected to reach due_at_km."""

    deadline: date | None
    """Whichever of the two comes first. This is the date a reminder goes out against."""

    days_left: int | None
    kilometres_left: int | None
    basis: DistanceBasis

    @property
    def needs_history(self) -> bool:
        return self.status is DueStatus.UNKNOWN


def add_months(start: date, months: int) -> date:
    """Shift a date by whole months, clamped to the end of the target month.

    Thirty-first of January plus one month is the twenty-eighth of February, not the third of
    March. Rolling over would quietly move a deadline into the following month.
    """
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, _days_in_month(year, month))
    return date(year, month, day)


def daily_distance(
    readings: list[Reading],
    annual_estimate: int | None = None,
) -> DailyDistance:
    """How far this car covers in a day.

    Measured from the odometer history when there is enough of it to mean anything, and otherwise
    from the figure the owner gave when adding the car. Which of the two was used is reported,
    because a date projected from two years of readings deserves more confidence than one
    projected from a guess, and the interface should be able to say which it is showing.
    """
    if len(readings) >= 2:
        ordered = sorted(readings, key=lambda reading: reading.on)
        first, last = ordered[0], ordered[-1]
        days = (last.on - first.on).days
        travelled = last.kilometres - first.kilometres

        if days >= MINIMUM_MEASURED_SPAN_DAYS and travelled > 0:
            return DailyDistance(travelled / days, DistanceBasis.MEASURED)

    if annual_estimate and annual_estimate > 0:
        return DailyDistance(annual_estimate / DAYS_PER_YEAR, DistanceBasis.ESTIMATED)

    return DailyDistance(None, DistanceBasis.NONE)


def next_due(
    interval: Interval,
    last_done: LastDone | None,
    current_kilometres: int,
    distance: DailyDistance,
    today: date,
    thresholds: Thresholds | None = None,
) -> Due:
    """When this item is next due on this car.

    `today` is passed in rather than read from the clock so that the result of this function
    depends on nothing but its arguments.
    """
    thresholds = thresholds or Thresholds()

    if last_done is None or not interval.exists:
        return Due(
            status=DueStatus.UNKNOWN,
            last_done=last_done,
            due_on=None,
            due_at_km=None,
            projected_on=None,
            deadline=None,
            days_left=None,
            kilometres_left=None,
            basis=distance.basis,
        )

    due_on = add_months(last_done.on, interval.months) if interval.months else None

    due_at_km: int | None = None
    if interval.kilometres is not None and last_done.kilometres is not None:
        due_at_km = last_done.kilometres + interval.kilometres

    kilometres_left = due_at_km - current_kilometres if due_at_km is not None else None

    projected_on: date | None = None
    if kilometres_left is not None:
        if kilometres_left <= 0:
            # Already past the mileage threshold, so the deadline was whenever that happened. The
            # exact day is unknown; today is the honest answer, and the status will say overdue.
            projected_on = today
        else:
            days = distance.days_to_cover(kilometres_left)
            projected_on = _shift(today, days) if days is not None else None

    deadline = _earliest(due_on, projected_on)
    days_left = (deadline - today).days if deadline is not None else None

    return Due(
        status=_status(days_left, kilometres_left, thresholds),
        last_done=last_done,
        due_on=due_on,
        due_at_km=due_at_km,
        projected_on=projected_on,
        deadline=deadline,
        days_left=days_left,
        kilometres_left=kilometres_left,
        basis=distance.basis,
    )


def _status(
    days_left: int | None, kilometres_left: int | None, thresholds: Thresholds
) -> DueStatus:
    """Whichever measure is more urgent decides.

    A car three days from a date deadline and eight thousand kilometres from a mileage one is due
    in three days. Being comfortable on one axis says nothing about the other.
    """
    if days_left is None and kilometres_left is None:
        return DueStatus.UNKNOWN

    if (days_left is not None and days_left < 0) or (
        kilometres_left is not None and kilometres_left <= 0
    ):
        return DueStatus.OVERDUE

    if (days_left is not None and days_left <= thresholds.days) or (
        kilometres_left is not None and kilometres_left <= thresholds.kilometres
    ):
        return DueStatus.SOON

    return DueStatus.OK


def _earliest(*candidates: date | None) -> date | None:
    known = [candidate for candidate in candidates if candidate is not None]
    return min(known) if known else None


def _shift(start: date, days: int) -> date:
    return start + timedelta(days=days)


def _days_in_month(year: int, month: int) -> int:
    return monthrange(year, month)[1]
