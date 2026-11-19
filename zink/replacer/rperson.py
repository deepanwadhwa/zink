from faker import Faker

from .base import ReplacementStrategy
from ..extractor import _DEFAULT_EXTRACTOR


class PersonReplacementStrategy(ReplacementStrategy):
    """Generate a synthetic name when the inference backend recognizes a name."""

    def __init__(self):
        self.faker = Faker()

    def replace(self, entity, original_label=None):
        """Return a name without shared tokens, or a redaction placeholder.

        Role labels can apply to a name or to a title. The default model
        checks the detected span for a name before generating a replacement.
        """
        original_text = entity.get("text", "").strip()
        if _DEFAULT_EXTRACTOR.predict(original_text, ("name",)):
            tokens = original_text.casefold().split()
            original_tokens = set(tokens)
            generate_name = (
                self.faker.name if len(tokens) > 1 else self.faker.first_name
            )
            for _ in range(10):
                candidate = generate_name()
                candidate_tokens = set(candidate.casefold().split())
                if candidate_tokens and original_tokens.isdisjoint(candidate_tokens):
                    return candidate

        return f"[{original_label}_REDACTED]"
