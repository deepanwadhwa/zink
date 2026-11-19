import re
from datetime import datetime, timedelta

from faker import Faker

from .base import ReplacementStrategy


SHORT_MONTHS = {
    "jan": "january",
    "feb": "february",
    "mar": "march",
    "apr": "april",
    "may": "may",
    "jun": "june",
    "jul": "july",
    "aug": "august",
    "sep": "september",
    "oct": "october",
    "nov": "november",
    "dec": "december",
}
_MONTH = re.compile(
    r"\b(?:" + "|".join(sorted(set(SHORT_MONTHS) | set(SHORT_MONTHS.values()))) + r")\b"
)
_WEEKDAY = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
)
_YEAR = re.compile(r"\b(?:19\d{2}|20\d{2})\b")
_DAY = re.compile(r"\b(?:0?[1-9]|[12][0-9]|3[01])\b")


def _different_value(generate, original):
    for _ in range(5):
        candidate = generate()
        if candidate != original:
            return candidate
    return None


def _numeric_dates(text):
    # A slash date may be month-first or day-first. Exclude both valid readings.
    original_dates = set()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            original_dates.add(datetime.strptime(text, pattern).date())
        except ValueError:
            pass
    return original_dates


class DateReplacementStrategy(ReplacementStrategy):
    """Generate synthetic dates without reusing the original components.

    Named months and weekdays keep their components when Faker can generate
    different values. Numeric dates and exhausted generations use ISO format
    and fall within the configured date range.
    """

    def __init__(
        self, start_date=datetime(1900, 1, 1), end_date=datetime(2100, 12, 31)
    ):
        self.start_date = (
            start_date.date() if isinstance(start_date, datetime) else start_date
        )
        self.end_date = end_date.date() if isinstance(end_date, datetime) else end_date
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        self.faker = Faker()

    def replace(self, entity):
        """Return a replacement string, or None if the source is the only choice."""
        original = entity.get("text", "").strip().lower()
        month = _MONTH.search(original)
        weekday = _WEEKDAY.search(original)
        if month is None and weekday is None:
            return self._bounded_iso_date(original)

        parts = []
        if month:
            original_month = SHORT_MONTHS.get(month[0], month[0])
            new_month = _different_value(
                lambda: self.faker.month_name().lower(), original_month
            )
            parts.append(new_month.capitalize() if new_month else None)

        day = _DAY.search(original)
        if day:
            new_day = _different_value(
                lambda: self.faker.random_int(min=1, max=28), int(day[0])
            )
            parts.append(str(new_day) if new_day is not None else None)
        elif weekday:
            new_weekday = _different_value(
                lambda: self.faker.day_of_week().lower(), weekday[0]
            )
            parts.append(new_weekday.capitalize() if new_weekday else None)

        year = _YEAR.search(original)
        if year:
            parts.append(_different_value(self.faker.year, year[0]))

        if all(parts):
            return " ".join(parts)
        return self._bounded_iso_date(original)

    def _bounded_iso_date(self, original):
        originals = _numeric_dates(original)
        start, end = self.start_date, self.end_date
        # Calendar offsets avoid timezone and timestamp conversions in Faker.
        offset = self.faker.random_int(min=0, max=(end - start).days)
        candidate = start + timedelta(days=offset)
        if candidate not in originals:
            return candidate.isoformat()

        # Choose a different in-range date if the provider drew the source date.
        while start in originals:
            if start >= end:
                return None
            start += timedelta(days=1)
        return start.isoformat()
