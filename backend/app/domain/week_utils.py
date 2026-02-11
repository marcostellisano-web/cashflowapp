"""Date and week utilities for production timeline calculations."""

from datetime import date, timedelta


def get_monday(d: date) -> date:
    """Return the Monday of the week containing the given date."""
    return d - timedelta(days=d.weekday())


def generate_week_mondays(start: date, end: date) -> list[date]:
    """Generate a list of week-commencing Mondays from start to end (inclusive).

    The first Monday is the Monday of the week containing `start`.
    The last Monday is the Monday of the week containing `end`.
    """
    first_monday = get_monday(start)
    last_monday = get_monday(end)
    mondays = []
    current = first_monday
    while current <= last_monday:
        mondays.append(current)
        current += timedelta(weeks=1)
    return mondays


def count_weekdays_in_week(monday: date, period_start: date, period_end: date) -> int:
    """Count the number of weekdays (Mon-Fri) in a given week that fall within a period.

    Returns a value between 0 and 5.
    """
    count = 0
    for offset in range(5):  # Mon=0 to Fri=4
        day = monday + timedelta(days=offset)
        if period_start <= day <= period_end:
            count += 1
    return count


def is_date_in_ranges(d: date, ranges: list[tuple[date, date]]) -> bool:
    """Check if a date falls within any of the given (start, end) ranges."""
    return any(start <= d <= end for start, end in ranges)
