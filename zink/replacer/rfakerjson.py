# newrfakerjson.py
from faker import Faker
from .json_mapping import JsonMappingReplacementStrategy
from .rdefault import DefaultReplacementStrategy
from .rdate import DateReplacementStrategy
from .rperson import PersonReplacementStrategy
from .vars import COUNTRIES_SYNONYMS, human_entity_roles
import random
# Read country names from file.
COUNTRY_NAMES = {name for country, synonyms in COUNTRIES_SYNONYMS.items() for name in [country] + synonyms}

# Define which labels are considered date-related.
DATE_LABELS = {
    "date", "month", "month name", "monthname", "day of week", "day_of_week", "weekday"
}

class FakerOrJsonReplacementStrategy:
    def __init__(self, label, use_json_mapping):
        # Normalize the label and initialize Faker.
        self.label = label.lower()
        self.faker = Faker()
        self.use_json_mapping = use_json_mapping

    def replace(self, entity):
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
            fake_value = PersonReplacementStrategy().replace(entity, original_label=self.label)
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
        if self.use_json_mapping:
            replacement = JsonMappingReplacementStrategy(self.label).replace(entity)
            return replacement, "json"
        else:
            replacement = DefaultReplacementStrategy().replace(entity)
            return replacement, "default"
