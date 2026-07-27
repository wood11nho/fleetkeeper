"""The arithmetic behind every reminder.

Nothing here touches a database. `today` is an argument rather than the clock, so each case states
its own situation completely and the results cannot drift with the calendar.
"""

from datetime import date

from fleetkeeper.schedule import (
    DailyDistance,
    DistanceBasis,
    DueStatus,
    Interval,
    LastDone,
    Reading,
    Thresholds,
    add_months,
    daily_distance,
    next_due,
)

TODAY = date(2026, 7, 27)


def rate(per_day: float) -> DailyDistance:
    """A known daily distance, so each case can state the pace it assumes."""
    return daily_distance(
        [Reading(date(2025, 7, 27), 0), Reading(date(2026, 7, 27), round(per_day * 365))]
    )


class TestAddMonths:
    def test_it_moves_whole_months(self) -> None:
        assert add_months(date(2026, 1, 15), 12) == date(2027, 1, 15)
        assert add_months(date(2026, 1, 15), 6) == date(2026, 7, 15)

    def test_the_end_of_a_month_is_clamped_rather_than_rolled_over(self) -> None:
        """The 31st of January plus a month is the 28th of February, not the 3rd of March.

        Rolling over would quietly push a deadline into the following month, which is the wrong
        direction for anything safety related.
        """
        assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
        assert add_months(date(2026, 3, 31), 1) == date(2026, 4, 30)

    def test_it_knows_about_leap_years(self) -> None:
        assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)


class TestDailyDistance:
    def test_it_measures_from_the_odometer_history(self) -> None:
        readings = [Reading(date(2026, 1, 1), 100_000), Reading(date(2026, 7, 1), 110_000)]

        distance = daily_distance(readings)

        assert distance.basis is DistanceBasis.MEASURED
        assert distance.per_day is not None
        assert round(distance.per_day) == 55

    def test_readings_too_close_together_are_not_trusted(self) -> None:
        """Two readings a week apart extrapolate to nonsense, so the owner's figure wins."""
        readings = [Reading(date(2026, 7, 20), 100_000), Reading(date(2026, 7, 27), 3_000)]

        distance = daily_distance(readings, annual_estimate=12_000)

        assert distance.basis is DistanceBasis.ESTIMATED

    def test_it_falls_back_to_the_declared_annual_distance(self) -> None:
        distance = daily_distance([], annual_estimate=18_000)

        assert distance.basis is DistanceBasis.ESTIMATED
        assert distance.per_day is not None
        assert round(distance.per_day) == 49

    def test_with_nothing_to_go_on_it_says_so(self) -> None:
        distance = daily_distance([])

        assert distance.basis is DistanceBasis.NONE
        assert distance.per_day is None
        assert distance.days_to_cover(5_000) is None

    def test_readings_that_go_nowhere_are_not_a_rate(self) -> None:
        """A car that has not moved between two readings does not travel zero km a day forever."""
        readings = [Reading(date(2026, 1, 1), 100_000), Reading(date(2026, 7, 1), 100_000)]

        assert daily_distance(readings, annual_estimate=10_000).basis is DistanceBasis.ESTIMATED

    def test_readings_out_of_order_are_sorted_first(self) -> None:
        readings = [Reading(date(2026, 7, 1), 110_000), Reading(date(2026, 1, 1), 100_000)]

        assert daily_distance(readings).basis is DistanceBasis.MEASURED


class TestNeverRecorded:
    def test_without_a_last_time_there_is_nothing_to_count_from(self) -> None:
        due = next_due(
            Interval(kilometres=15_000, months=12),
            last_done=None,
            current_kilometres=200_000,
            distance=rate(40),
            today=TODAY,
        )

        assert due.status is DueStatus.UNKNOWN
        assert due.needs_history
        assert due.deadline is None

    def test_an_item_with_no_interval_produces_no_deadline(self) -> None:
        """A clutch is replaced when it fails. Inventing a date for it would be a lie."""
        due = next_due(
            Interval(kilometres=None, months=None),
            last_done=LastDone(date(2025, 1, 1), 180_000),
            current_kilometres=200_000,
            distance=rate(40),
            today=TODAY,
        )

        assert due.status is DueStatus.UNKNOWN
        assert due.deadline is None


class TestTimeOnly:
    """Brake fluid: two years, no mileage figure at all."""

    def test_it_counts_from_the_last_time(self) -> None:
        due = next_due(
            Interval(kilometres=None, months=24),
            last_done=LastDone(date(2025, 3, 10), None),
            current_kilometres=200_000,
            distance=rate(40),
            today=TODAY,
        )

        assert due.due_on == date(2027, 3, 10)
        assert due.deadline == date(2027, 3, 10)
        assert due.due_at_km is None
        assert due.status is DueStatus.OK

    def test_a_passed_date_is_overdue(self) -> None:
        due = next_due(
            Interval(kilometres=None, months=24),
            last_done=LastDone(date(2024, 1, 10), None),
            current_kilometres=200_000,
            distance=rate(40),
            today=TODAY,
        )

        assert due.status is DueStatus.OVERDUE
        assert due.days_left is not None and due.days_left < 0

    def test_a_date_within_the_warning_window_is_due_soon(self) -> None:
        due = next_due(
            Interval(kilometres=None, months=12),
            last_done=LastDone(date(2025, 8, 10), None),
            current_kilometres=200_000,
            distance=rate(40),
            today=TODAY,
        )

        assert due.deadline == date(2026, 8, 10)
        assert due.status is DueStatus.SOON


class TestMileageOnly:
    """Spark plugs at 40,000 km, with no calendar interval."""

    def test_the_threshold_becomes_a_date_using_the_daily_distance(self) -> None:
        due = next_due(
            Interval(kilometres=40_000, months=None),
            last_done=LastDone(date(2024, 1, 1), 180_000),
            current_kilometres=200_000,
            distance=rate(50),
            today=TODAY,
        )

        assert due.due_at_km == 220_000
        assert due.kilometres_left == 20_000
        # 20,000 km left at roughly 50 a day is about 400 days.
        assert due.projected_on is not None
        assert 380 <= (due.projected_on - TODAY).days <= 420
        assert due.deadline == due.projected_on

    def test_passing_the_threshold_is_overdue_whatever_the_date_says(self) -> None:
        due = next_due(
            Interval(kilometres=40_000, months=None),
            last_done=LastDone(date(2026, 7, 1), 180_000),
            current_kilometres=225_000,
            distance=rate(50),
            today=TODAY,
        )

        assert due.kilometres_left is not None and due.kilometres_left < 0
        assert due.status is DueStatus.OVERDUE

    def test_being_close_in_kilometres_is_due_soon(self) -> None:
        due = next_due(
            Interval(kilometres=15_000, months=None),
            last_done=LastDone(date(2026, 1, 1), 190_000),
            current_kilometres=204_500,
            distance=rate(50),
            today=TODAY,
        )

        assert due.kilometres_left == 500
        assert due.status is DueStatus.SOON

    def test_without_a_mileage_for_the_last_time_the_threshold_cannot_be_placed(self) -> None:
        """Someone who recorded an oil change from memory may not know the odometer reading."""
        due = next_due(
            Interval(kilometres=15_000, months=None),
            last_done=LastDone(date(2026, 1, 1), None),
            current_kilometres=200_000,
            distance=rate(50),
            today=TODAY,
        )

        assert due.due_at_km is None
        assert due.status is DueStatus.UNKNOWN

    def test_with_no_daily_distance_the_threshold_has_no_date(self) -> None:
        due = next_due(
            Interval(kilometres=15_000, months=None),
            last_done=LastDone(date(2026, 1, 1), 190_000),
            current_kilometres=195_000,
            distance=daily_distance([]),
            today=TODAY,
        )

        assert due.kilometres_left == 10_000
        assert due.projected_on is None
        assert due.deadline is None
        assert due.status is DueStatus.OK


class TestWhicheverComesFirst:
    """Oil: 15,000 km or 12 months. This is the shape of a real service schedule."""

    def test_the_date_wins_for_a_car_that_barely_moves(self) -> None:
        due = next_due(
            Interval(kilometres=15_000, months=12),
            last_done=LastDone(date(2025, 9, 1), 100_000),
            current_kilometres=103_000,
            distance=rate(8),
            today=TODAY,
        )

        assert due.due_on == date(2026, 9, 1)
        assert due.projected_on is not None and due.projected_on > due.due_on
        assert due.deadline == due.due_on

    def test_the_mileage_wins_for_a_car_that_covers_ground(self) -> None:
        due = next_due(
            Interval(kilometres=15_000, months=12),
            last_done=LastDone(date(2026, 6, 1), 100_000),
            current_kilometres=108_000,
            distance=rate(120),
            today=TODAY,
        )

        assert due.due_on == date(2027, 6, 1)
        assert due.projected_on is not None and due.projected_on < due.due_on
        assert due.deadline == due.projected_on

    def test_comfortable_on_one_measure_is_not_comfortable_overall(self) -> None:
        """Three days from a date and eight thousand kilometres away is due in three days."""
        due = next_due(
            Interval(kilometres=15_000, months=12),
            last_done=LastDone(date(2025, 7, 30), 100_000),
            current_kilometres=107_000,
            distance=rate(20),
            today=TODAY,
        )

        assert due.kilometres_left == 8_000
        assert due.days_left == 3
        assert due.status is DueStatus.SOON


class TestThresholds:
    def test_the_warning_window_can_be_widened(self) -> None:
        interval = Interval(kilometres=None, months=12)
        last = LastDone(date(2025, 9, 15), None)

        default = next_due(interval, last, 200_000, rate(40), TODAY)
        patient = next_due(
            interval,
            last,
            200_000,
            rate(40),
            TODAY,
            thresholds=Thresholds(days=60, kilometres=1_000),
        )

        assert default.status is DueStatus.OK
        assert patient.status is DueStatus.SOON

    def test_the_basis_of_the_projection_is_reported(self) -> None:
        """A date projected from two years of readings deserves more trust than one from a guess."""
        from_readings = next_due(
            Interval(kilometres=15_000, months=None),
            LastDone(date(2026, 1, 1), 190_000),
            195_000,
            daily_distance(
                [Reading(date(2025, 1, 1), 150_000), Reading(date(2026, 1, 1), 190_000)]
            ),
            TODAY,
        )
        from_a_guess = next_due(
            Interval(kilometres=15_000, months=None),
            LastDone(date(2026, 1, 1), 190_000),
            195_000,
            daily_distance([], annual_estimate=40_000),
            TODAY,
        )

        assert from_readings.basis is DistanceBasis.MEASURED
        assert from_a_guess.basis is DistanceBasis.ESTIMATED
