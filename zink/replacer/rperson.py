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
        Replace the text of a person-related entity with a realistic name.
        Args:
            entity (dict): The entity to be replaced.
            original_label (str, optional): The original label of the entity. Defaults to None.
        Returns:
            str: The replaced text.
        """
        original_text = entity.get("text", "").strip()
        # Use the default extractor to check if the text is recognized as a name.
        name_ = _DEFAULT_EXTRACTOR.predict(original_text, ("name",))
        if name_:
            # If more than one token, generate a full name; otherwise, a first name.
            if len(original_text.split(" ")) > 1:
                fake_value = self.faker.name()
            else:
                fake_value = self.faker.first_name()
            if fake_value.strip() != original_text:
                return fake_value
        # Fallback if extraction didn't confirm a name.
        return f"[{original_label}_REDACTED]"
