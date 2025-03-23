# newrfakerjson.py
from faker import Faker
from .json_mapping import JsonMappingReplacementStrategy
from .rdefault import DefaultReplacementStrategy
from .rdate import DateReplacementStrategy
from .rperson import PersonReplacementStrategy
from .vars import COUNTRIES_SYNONYMS, human_entity_roles
import random

# Read country names from file.
COUNTRY_NAMES = {
    name
    for country, synonyms in COUNTRIES_SYNONYMS.items()
    for name in [country] + synonyms
}

# Define which labels are considered date-related.
DATE_LABELS = {
    "date",
    "month",
    "month name",
    "monthname",
    "day of week",
    "day_of_week",
    "weekday",
}


class FakerOrJsonReplacementStrategy:
    """
    Replaces entities using Faker, JSON mappings, or default strategies.

    This class provides a flexible replacement strategy that prioritizes
    using Faker methods when available, falls back to JSON mappings if
    `use_json_mapping` is True, and finally uses a default replacement
    strategy if no other method is successful.  It also handles specific
    cases for dates and locations.

    :param label: The entity label (e.g., "person", "location", "date").
        This will be converted to lowercase.

    :type label: str

    :param use_json_mapping: Whether to use JSON-based mappings as a
        fallback if Faker cannot generate a replacement.

    :type use_json_mapping: bool
    """
    def __init__(self, label, use_json_mapping):
        """
        Initializes the FakerOrJsonReplacementStrategy.
        """
        # Normalize the label and initialize Faker.
        self.label = label.lower()
        self.faker = Faker()
        self.use_json_mapping = use_json_mapping

    def replace(self, entity):
        """
        Replaces the given entity with a pseudonym.

        This method attempts to replace the entity's text using the
        following strategies, in order:

        1.  Date Replacement: If the label is date-related, uses
            `DateReplacementStrategy`.
        2.  Country Replacement: If the label is "location" and the text
            is a recognized country name, replaces it with a different
            country name.
        3.  Person Replacement: If the label is a person-related role
            (e.g., "doctor", "nurse"), uses `PersonReplacementStrategy`.
        4.  Faker Method: If Faker has a method matching the label (e.g.,
            `faker.address()` for the label "address"), uses that method.
        5.  Faker Person/Location: As a special case, if the label is "person" it tries to use `self.faker.name()`. If the label is
            "location", it tries using `self.faker.city()`
        6.  Fallback: If none of the above work, uses either
            `JsonMappingReplacementStrategy` (if `use_json_mapping` is
            True) or `DefaultReplacementStrategy`.

        :param entity: A dictionary representing the entity, containing
            at least a "text" key.
        :type entity: dict
        :return: A tuple containing the replacement text and a string
            indicating which strategy was used (e.g., "faker", "json",
            "default", "rdate", "faker_country", "rperson").
        :rtype: tuple(str, str)

        """
        original_text = entity.get("text", "").strip()

        # Delegate all date-related labels to DateReplacementStrategy.
        if self.label in DATE_LABELS:
            replacement = DateReplacementStrategy().replace(entity)
            return replacement, "rdate"

        # Special case for location: if the text is a country name.
        if self.label == "location" and original_text.lower() in COUNTRY_NAMES:
            candidates = list(COUNTRY_NAMES - {original_text.lower()})
            if candidates:
                return random.choice(candidates).title(), "faker_country"
            else:
                return self._fallback(entity)

        # Delegate person-related labels to PersonReplacementStrategy.
        if self.label in human_entity_roles:
            fake_value = PersonReplacementStrategy().replace(
                entity, original_label=self.label
            )
            if fake_value.strip() != original_text:
                return fake_value, "rperson"

        # General case: if Faker provides a method matching the label.
        if self.label in dir(self.faker):
            faker_method = getattr(self.faker, self.label)
            if callable(faker_method):
                try:
                    fake_value = faker_method()
                    if fake_value.strip() != original_text:
                        return fake_value, "faker"
                except Exception:
                    pass

        # Fallback for "person" and for locations not recognized as a country.
        if self.label == "person" and "name" in dir(self.faker):
            try:
                fake_value = self.faker.name()
                if fake_value.strip() != original_text:
                    return fake_value, "faker"
            except Exception:
                pass
        if self.label == "location" and "city" in dir(self.faker):
            try:
                fake_value = self.faker.city()
                if fake_value.strip() != original_text:
                    return fake_value, "faker"
            except Exception:
                pass

        # Final fallback.
        return self._fallback(entity)

    def _fallback(self, entity):
        """
        Provides a fallback replacement strategy.

        This method is called if no other replacement strategy is
        successful.  It uses either `JsonMappingReplacementStrategy` (if
        `use_json_mapping` is True) or `DefaultReplacementStrategy`.

        :param entity: A dictionary representing the entity.
        :type entity: dict
        :return: The replacement text from the fallback strategy.
        :rtype: str
        """
        if self.use_json_mapping:
            replacement = JsonMappingReplacementStrategy(self.label).replace(entity)
            return replacement, "json"
        else:
            replacement = DefaultReplacementStrategy().replace(entity)
            return replacement, "default"
