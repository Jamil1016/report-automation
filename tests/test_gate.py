from datetime import date

from team_activity_report.gate import is_holiday, is_weekend, should_run


class TestIsWeekend:
    def test_saturday(self) -> None:
        # 2026-05-23 is a Saturday
        assert is_weekend(date(2026, 5, 23)) is True

    def test_sunday(self) -> None:
        # 2026-05-24 is a Sunday
        assert is_weekend(date(2026, 5, 24)) is True

    def test_monday(self) -> None:
        # 2026-05-25 is Memorial Day (Mon) — still not weekend
        assert is_weekend(date(2026, 5, 25)) is False

    def test_wednesday(self) -> None:
        assert is_weekend(date(2026, 5, 27)) is False


class TestIsHoliday:
    def test_new_years_day(self) -> None:
        assert is_holiday(date(2026, 1, 1)) is True

    def test_memorial_day(self) -> None:
        assert is_holiday(date(2026, 5, 25)) is True

    def test_christmas(self) -> None:
        assert is_holiday(date(2026, 12, 25)) is True

    def test_random_workday(self) -> None:
        assert is_holiday(date(2026, 5, 27)) is False


class TestShouldRun:
    def test_weekday_runs(self) -> None:
        # 2026-05-26 is a Tuesday, not a holiday
        ok, reason = should_run(date(2026, 5, 26))
        assert ok is True
        assert reason == "weekday"

    def test_weekend_skips(self) -> None:
        ok, reason = should_run(date(2026, 5, 23))
        assert ok is False
        assert reason == "weekend"

    def test_holiday_skips(self) -> None:
        ok, reason = should_run(date(2026, 5, 25))
        assert ok is False
        assert reason == "holiday"

    def test_holiday_on_weekend_reports_as_weekend(self) -> None:
        # If a holiday happens to fall on a weekend, weekend wins (it's checked first)
        # 2026-07-04 is a Saturday
        ok, reason = should_run(date(2026, 7, 4))
        assert ok is False
        assert reason == "weekend"
