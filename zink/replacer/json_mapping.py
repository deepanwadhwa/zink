import json
import random
import gzip
import importlib.resources as resources  # available in Python 3.7+
from functools import lru_cache
from .base import ReplacementStrategy


@lru_cache(maxsize=1)
def load_mapping():
    """Read bundled fallback values on demand, without writing a user cache."""
    with (
        resources.files("zink.data")
        .joinpath("replacements.json.gzip")
        .open("rb") as source
    ):
        with gzip.open(source, "rt", encoding="utf-8") as stream:
            return json.load(stream)


class JsonMappingReplacementStrategy(ReplacementStrategy):
    def __init__(self, label):
        # Store the label in lowercase.
        self.label = label.lower()

    def replace(self, entity):
        candidates = load_mapping().get(self.label)
        if candidates and isinstance(candidates, list):
            first_random = random.choice(candidates)
            if first_random != entity["text"]:
                return first_random
            second_random = random.choice(candidates)
            if second_random != entity["text"]:
                return second_random
            return "[REDACTED]"
        return "[REDACTED]"
