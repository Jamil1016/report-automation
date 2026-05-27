"""Weekday + holiday gate. Pure functions, no IO."""

from __future__ import annotations

from datetime import date

# 2026 US federal holidays (when the federal government observes them).
# When a holiday falls on a weekend, the observed date may shift — this list
# reflects the actual calendar holiday, not the observed shift.
_HOLIDAYS_2026: frozenset[date] = frozenset(
    {
        date(2026, 1, 1),  # New Year's Day
        date(2026, 1, 19),  # Martin Luther King Jr. Day
        date(2026, 2, 16),  # Presidents Day
        date(2026, 5, 25),  # Memorial Day
        date(2026, 6, 19),  # Juneteenth
        date(2026, 7, 4),  # Independence Day (Saturday in 2026; observed Fri 7/3)
        date(2026, 9, 7),  # Labor Day
        date(2026, 10, 12),  # Columbus Day
        date(2026, 11, 11),  # Veterans Day
        date(2026, 11, 26),  # Thanksgiving
        date(2026, 12, 25),  # Christmas
    }
)


def is_weekend(d: date) -> bool:
    """Saturday (5) or Sunday (6)."""
    return d.weekday() >= 5


def is_holiday(d: date) -> bool:
    """True if d is a US federal holiday in 2026."""
    return d in _HOLIDAYS_2026


def should_run(d: date) -> tuple[bool, str]:
    """Return (True, 'weekday'), (False, 'weekend'), or (False, 'holiday').

    Weekend is checked before holiday so weekend-falling holidays report as weekend.
    """
    if is_weekend(d):
        return False, "weekend"
    if is_holiday(d):
        return False, "holiday"
    return True, "weekday"
