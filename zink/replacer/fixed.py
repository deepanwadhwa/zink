
import random
from .base import ReplacementStrategy

class FixedReplacementStrategy(ReplacementStrategy):
    def __init__(self, fixed_value):
        # If the user provides a single string, wrap it in a list.
        if isinstance(fixed_value, list):
            self.fixed_values = fixed_value
        else:
            self.fixed_values = [fixed_value]

    def replace(self, entity):
        return random.choice(self.fixed_values)

