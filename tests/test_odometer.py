"""Measuring a car's pace and filling in the odometer for days nobody wrote down.

Nothing here touches a database, and `today` is an argument rather than the clock, so every case
states its own situation completely.

The figures in `GOLF` are the real readings of the family's 2005 Golf Plus, kept rather than
rounded off: they are the case the module was written for, and a case taken from life catches
what a tidy example does not.
"""

from datetime import date

from fleetkeeper.odometer import (
    MileageBasis,
    Pace,
    bracket,
    contradiction,
    kilometres_on,
    pace,
    series,
)
from fleetkeeper.schedule import DistanceBasis, Reading

TODAY = date(2026, 7, 27)

GOLF = [
    Reading(date(2025, 10, 20), 281_762),
    Reading(date(2026, 2, 19), 286_442),
    Reading(date(2026, 7, 27), 290_000),
]


def golf_pace() -> Pace:
    return pace(GOLF, today=TODAY)


class TestSeries:
    def test_the_same_day_from_two_places_keeps_the_higher_reading(self) -> None:
        """An intervention and a reading of its own can both speak for the same day."""
        ordered = series(
            [
                Reading(date(2026, 2, 19), 286_442),
                Reading(date(2026, 2, 19), 286_400),
            ]
        )

        assert ordered == [Reading(date(2026, 2, 19), 286_442)]

    def test_a_reading_below_an_earlier_one_is_dropped(self) -> None:
        """An odometer does not go backwards, so the low figure is a typing mistake.

        Keeping it would produce a negative rate and push every deadline into the past.
        """
        ordered = series(
            [
                Reading(date(2026, 1, 1), 280_000),
                Reading(date(2026, 3, 1), 28_000),
                Reading(date(2026, 6, 1), 285_000),
            ]
        )

        assert [reading.kilometres for reading in ordered] == [280_000, 285_000]

    def test_readings_may_arrive_in_any_order(self) -> None:
        ordered = series([GOLF[2], GOLF[0], GOLF[1]])

        assert ordered == GOLF

    def test_a_brand_new_car_reads_zero(self) -> None:
        ordered = series([Reading(date(2026, 1, 1), 0), Reading(date(2026, 6, 1), 4_000)])

        assert [reading.kilometres for reading in ordered] == [0, 4_000]


class TestPace:
    def test_three_readings_are_fitted_with_a_trend(self) -> None:
        """Least squares through all three, which is 29.09 km a day on these readings."""
        rate = golf_pace()

        assert rate.distance.basis is DistanceBasis.MEASURED
        assert rate.readings_used == 3
        assert rate.span_days == 280
        assert rate.distance.per_day is not None
        assert round(rate.distance.per_day, 2) == 29.09

    def test_the_trend_is_not_the_line_between_the_ends(self) -> None:
        """The straight line between the ends gives 29.42, and the middle reading pulls it down.

        A small difference here, which is itself worth knowing: this car covers ground steadily.
        Where it matters is a mistyped digit at either end, which defines the answer with two
        readings and only bends it with three.
        """
        rate = golf_pace()
        between_ends = (290_000 - 281_762) / 280

        assert rate.distance.per_day is not None
        assert round(between_ends, 2) == 29.42
        assert rate.distance.per_day < between_ends

    def test_two_readings_measure_between_the_ends(self) -> None:
        readings = [Reading(date(2026, 1, 1), 100_000), Reading(date(2026, 7, 1), 110_000)]

        rate = pace(readings, today=TODAY)

        assert rate.distance.basis is DistanceBasis.MEASURED
        assert rate.readings_used == 2
        assert rate.distance.per_day is not None
        assert round(rate.distance.per_day) == 55

    def test_only_the_last_two_years_are_fitted_when_there_are_enough_of_them(self) -> None:
        """A commute given up three years ago says nothing about the car as it is driven now."""
        readings = [
            Reading(date(2023, 1, 1), 0),
            Reading(date(2025, 1, 1), 100_000),
            Reading(date(2025, 10, 1), 110_000),
            Reading(date(2026, 7, 1), 120_000),
        ]

        rate = pace(readings, today=TODAY)

        assert rate.readings_used == 3
        assert rate.span_days == (date(2026, 7, 1) - date(2025, 1, 1)).days

    def test_with_too_few_recent_readings_the_whole_history_is_used(self) -> None:
        """Two readings inside the window cannot show a trend, so the older ones are let back in.

        Something measured beats the owner's own guess even when it reaches further back than
        we would like.
        """
        readings = [
            Reading(date(2023, 1, 1), 100_000),
            Reading(date(2026, 1, 1), 200_000),
            Reading(date(2026, 7, 1), 203_000),
        ]

        rate = pace(readings, today=TODAY, annual_estimate=12_000)

        assert rate.distance.basis is DistanceBasis.MEASURED
        assert rate.readings_used == 3

    def test_readings_too_close_together_are_not_trusted(self) -> None:
        """Two readings a week apart extrapolate to nonsense, so the owner's figure wins."""
        readings = [Reading(date(2026, 7, 20), 100_000), Reading(date(2026, 7, 27), 100_400)]

        rate = pace(readings, today=TODAY, annual_estimate=12_000)

        assert rate.distance.basis is DistanceBasis.ESTIMATED

    def test_readings_that_go_nowhere_are_not_a_rate(self) -> None:
        """A car that has not moved does not travel zero kilometres a day for ever."""
        readings = [
            Reading(date(2026, 1, 1), 100_000),
            Reading(date(2026, 4, 1), 100_000),
            Reading(date(2026, 7, 1), 100_000),
        ]

        rate = pace(readings, today=TODAY, annual_estimate=10_000)

        assert rate.distance.basis is DistanceBasis.ESTIMATED

    def test_it_falls_back_to_the_declared_annual_distance(self) -> None:
        rate = pace([], today=TODAY, annual_estimate=18_000)

        assert rate.distance.basis is DistanceBasis.ESTIMATED
        assert rate.distance.per_day is not None
        assert round(rate.distance.per_day) == 49

    def test_with_nothing_to_go_on_it_says_so(self) -> None:
        rate = pace([], today=TODAY)

        assert rate.distance.basis is DistanceBasis.NONE
        assert rate.distance.per_day is None
        assert rate.readings_used == 0
        assert rate.span_days == 0


class TestKilometresOn:
    def test_a_day_with_a_reading_is_not_an_estimate(self) -> None:
        estimate = kilometres_on(GOLF, date(2026, 2, 19), golf_pace())

        assert estimate.kilometres == 286_442
        assert estimate.basis is MileageBasis.RECORDED
        assert estimate.is_recorded

    def test_a_day_between_two_readings_is_interpolated(self) -> None:
        """The wheel alignment of the 6th of July, recorded without a mileage.

        Between 286,442 on the 19th of February and 290,000 on the 27th of July, the odometer
        was certainly somewhere in between, and 137 of those 158 days had passed.
        """
        estimate = kilometres_on(GOLF, date(2026, 7, 6), golf_pace())

        assert estimate.kilometres == 289_527
        assert estimate.basis is MileageBasis.INTERPOLATED
        assert not estimate.is_recorded

    def test_interpolation_uses_the_two_readings_around_the_day(self) -> None:
        """Not the ends of the whole history: the nearest pair bounds the answer tightest."""
        estimate = kilometres_on(GOLF, date(2025, 12, 1), golf_pace())

        assert estimate.kilometres is not None
        assert 281_762 < estimate.kilometres < 286_442

    def test_a_day_after_the_last_reading_is_projected_forward(self) -> None:
        estimate = kilometres_on(GOLF, date(2026, 8, 26), golf_pace())

        assert estimate.basis is MileageBasis.PROJECTED
        assert estimate.kilometres is not None
        # Thirty days at roughly 29 a day.
        assert 290_800 <= estimate.kilometres <= 290_950

    def test_a_day_before_the_first_reading_is_projected_backwards(self) -> None:
        estimate = kilometres_on(GOLF, date(2025, 8, 20), golf_pace())

        assert estimate.basis is MileageBasis.PROJECTED
        assert estimate.kilometres is not None
        # Sixty-one days before the first reading, at roughly 29 a day.
        assert 279_900 <= estimate.kilometres <= 280_050

    def test_it_never_projects_below_zero(self) -> None:
        readings = [Reading(date(2026, 1, 1), 5_000), Reading(date(2026, 7, 1), 8_000)]

        estimate = kilometres_on(readings, date(2023, 1, 1), pace(readings, today=TODAY))

        assert estimate.kilometres == 0

    def test_it_gives_nothing_for_a_day_before_the_car_existed(self) -> None:
        estimate = kilometres_on(GOLF, date(2004, 6, 1), golf_pace(), began=date(2005, 1, 1))

        assert estimate.kilometres is None
        assert estimate.basis is MileageBasis.NONE

    def test_the_start_of_the_car_does_not_block_a_later_day(self) -> None:
        estimate = kilometres_on(GOLF, date(2025, 8, 20), golf_pace(), began=date(2005, 1, 1))

        assert estimate.basis is MileageBasis.PROJECTED

    def test_without_a_rate_there_is_nothing_to_project_from(self) -> None:
        readings = [Reading(date(2026, 7, 27), 230_000)]

        estimate = kilometres_on(readings, date(2026, 1, 1), pace(readings, today=TODAY))

        assert estimate.kilometres is None
        assert estimate.basis is MileageBasis.NONE

    def test_a_single_reading_still_speaks_for_its_own_day(self) -> None:
        readings = [Reading(date(2026, 7, 27), 230_000)]

        estimate = kilometres_on(readings, date(2026, 7, 27), pace(readings, today=TODAY))

        assert estimate.kilometres == 230_000
        assert estimate.basis is MileageBasis.RECORDED

    def test_without_any_readings_there_is_nothing_to_say(self) -> None:
        estimate = kilometres_on([], TODAY, pace([], today=TODAY, annual_estimate=12_000))

        assert estimate.kilometres is None
        assert estimate.basis is MileageBasis.NONE


class TestContradiction:
    """Proving a recalled figure wrong, which is possible far more often than guessing it right."""

    def test_a_figure_below_an_earlier_reading_is_impossible(self) -> None:
        ruled_out = contradiction(GOLF, date(2026, 4, 1), 250_000)

        assert ruled_out is not None
        assert ruled_out.at_least == GOLF[1]
        assert ruled_out.at_most == GOLF[2]

    def test_a_figure_above_a_later_reading_is_impossible(self) -> None:
        ruled_out = contradiction(GOLF, date(2026, 4, 1), 295_000)

        assert ruled_out is not None
        assert ruled_out.at_most == GOLF[2]

    def test_a_figure_inside_the_readings_could_be_true(self) -> None:
        assert contradiction(GOLF, date(2026, 2, 19), 286_442) is None
        assert contradiction(GOLF, date(2026, 4, 1), 288_000) is None

    def test_a_figure_below_one_already_written_for_that_day_is_impossible(self) -> None:
        """The case that prompted this: a mileage typed from memory onto a day already recorded."""
        ruled_out = contradiction(GOLF, date(2026, 2, 19), 286_000)

        assert ruled_out is not None
        assert ruled_out.at_least == GOLF[1]

    def test_a_higher_figure_for_a_day_already_written_could_be_true(self) -> None:
        """An errand later the same day is not a contradiction."""
        assert contradiction(GOLF, date(2026, 2, 19), 286_500) is None

    def test_a_figure_above_everything_known_could_be_true(self) -> None:
        """Nothing bounds the future, so a reading past the last one is simply new."""
        assert contradiction(GOLF, date(2026, 9, 1), 300_000) is None

    def test_nothing_can_be_ruled_out_without_readings(self) -> None:
        assert contradiction([], date(2026, 2, 19), 1_000_000) is None

    def test_the_bracket_is_open_at_the_bottom_before_the_first_reading(self) -> None:
        box = bracket(GOLF, date(2025, 1, 1))

        assert box.at_least is None
        assert box.at_most == GOLF[0]
