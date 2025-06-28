# rperson.py
from faker import Faker
from .base import ReplacementStrategy
from ..extractor import _DEFAULT_EXTRACTOR


class PersonReplacementStrategy(ReplacementStrategy):
    """
    Replacement strategy for person-related entities.
    This strategy uses the Faker library to generate realistic names.

    Attributes:
        faker (Faker): An instance of the Faker class for generating names.
    """

    def __init__(self):
        self.faker = Faker()

    def replace(self, entity, original_label=None):
        """
        Replace the text of a person-related entity with a realistic name,
        ensuring the Faker-generated name does not match or share tokens
        with the original.

        Args:
            entity (dict): The entity to be replaced.
            original_label (str, ): The original label of the entity. Defaults to None.

        Returns:
            str: The replaced text.
        """
        original_text = entity.get("text", "").strip()
        name_ = _DEFAULT_EXTRACTOR.predict(original_text, ("name",))
        if name_:
            # Split original into tokens for comparison
            original_tokens = set(original_text.lower().split())

            # If multiple tokens, generate a full name; otherwise, generate a first name.
            if len(original_text.split()) > 1:
                for _ in range(10):
                    fake_value = self.faker.name()  # full name
                    fake_tokens = set(fake_value.lower().split())
                    # Check if any token overlaps with the original
                    if original_tokens.isdisjoint(fake_tokens):
                        return fake_value
                # Fallback if we can’t find a unique name
                return f"[{original_label}_REDACTED]"
            else:
                # Single token scenario
                for _ in range(10):
                    fake_value = self.faker.first_name()  # single first name
                    if list(original_tokens)[0].lower() not in fake_value.lower() or fake_value.lower() not in list(original_tokens)[0].lower():
                        return fake_value
                # Fallback
                return f"[{original_label}_REDACTED]"

        # If no name recognized or no fallback, redact
        return f"[{original_label}_REDACTED]"

