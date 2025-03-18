# rdate.py
from datetime import datetime, timedelta
import re
import random
from faker import Faker
from .base import ReplacementStrategy

# Known full month names in English.
KNOWN_MONTH_NAMES = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
}

# Known short month synonyms.
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
    "dec": "december"
}

# Known days of the week.
KNOWN_DAYS_OF_WEEK = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
}

class DateReplacementStrategy(ReplacementStrategy):
    def __init__(self, start_date=datetime(1900, 1, 1), end_date=datetime(2100, 12, 31)):
        self.start_date = start_date
        self.end_date = end_date
        self.faker = Faker()

    def replace(self, entity):
        original_text = entity.get("text", "").strip().lower()

        # If there's no explicit (alphabetic) month name present, assume the date is purely numeric
        # and simply return a faker-generated date.
        if not (any(month in original_text.lower() for month in KNOWN_MONTH_NAMES) or 
                any(month in original_text.lower() for month in SHORT_MONTHS.keys())):
            return self.faker.date()


        # Otherwise, proceed with custom extraction.
        month_component = None
        day_component = None
        year_component = None

        # Check for a short month (e.g. "jan") and convert it to its full name.
        for short, full in SHORT_MONTHS.items():
            if re.search(r'\b' + re.escape(short) + r'\b', original_text):
                month_component = full
                break

        # If no short month found, look for a full month name.
        if not month_component:
            for m in KNOWN_MONTH_NAMES:
                if m in original_text:
                    month_component = m
                    break

        # Extract a 4-digit year.
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', original_text)
        if year_match:
            year_component = year_match.group(0)

        # Extract a day number (ensuring it's not part of the year).
        day_match = re.search(r'\b([0-2]?[0-9]|3[0-1])\b', original_text)
        if day_match and len(day_match.group(0)) < 4:
            day_component = day_match.group(0)

        # Alternatively, check for a day name.
        if not day_component:
            for d in KNOWN_DAYS_OF_WEEK:
                if re.search(r'\b' + re.escape(d) + r'\b', original_text):
                    day_component = d
                    break

        # Generate new components using Faker.
        new_month = None
        new_day = None
        new_year = None

        if month_component:
            for _ in range(5):
                fake_month = self.faker.month_name().lower()
                if fake_month != month_component:
                    new_month = fake_month.capitalize()
                    break

        if year_component:
            for _ in range(5):
                fake_year = self.faker.year()
                if fake_year != year_component:
                    new_year = fake_year
                    break

        if day_component:
            try:
                int(day_component)
                for _ in range(5):
                    fake_day = str(self.faker.random_int(min=1, max=28))
                    if fake_day != day_component:
                        new_day = fake_day
                        break
            except ValueError:
                for _ in range(5):
                    fake_day = self.faker.day_of_week().lower()
                    if fake_day != day_component:
                        new_day = fake_day.capitalize()
                        break

        # Reassemble the new date string (order: Month, Day, Year).
        new_date_parts = []
        if new_month:
            new_date_parts.append(new_month)
        if new_day:
            new_date_parts.append(new_day)
        if new_year:
            new_date_parts.append(new_year)
        new_date = " ".join(new_date_parts)

        if new_date:
            return new_date
        else:
            # Fallback: return a completely random date.
            delta = self.end_date - self.start_date
            random_days = random.randint(0, delta.days)
            random_date = self.start_date + timedelta(days=random_days)
            return random_date.strftime("%Y-%m-%d")
