

import json
import random
from .base import ReplacementStrategy

def load_mapping(json_filename="data/replacements.json"):
    try:
        with open(json_filename) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON mapping: {e}")
        return {}

# Load mapping globally so it is loaded only once.
GLOBAL_MAPPING = load_mapping()

class JsonMappingReplacementStrategy(ReplacementStrategy):
    def __init__(self, label):
        # Store the label in lowercase.
        self.label = label.lower()

    def replace(self, entity):
        candidates = GLOBAL_MAPPING.get(self.label)
        if candidates and isinstance(candidates, list):
            first_random = random.choice(candidates)
            # Ensure the replacement is not the same as the original text.
            if first_random != entity['text']:
                return first_random
            # If the first random choice is the same, try again.
            second_random = random.choice(candidates)
            if second_random != entity['text']:
                return second_random
            # If both random choices are the same, return a different candidate.
            return "[REDACTED]"
        # If the label is not found in the mapping, return a default placeholder.
        return "[REDACTED]"
