from .base import ReplacementStrategy
import random

class PersonReplacementStrategy(ReplacementStrategy):
    def __init__(self, pseudonyms=None):
        if pseudonyms is None:
            pseudonyms = ["Alice", "Bob", "Charlie", "Diana"]
        self.pseudonyms = pseudonyms

    def replace(self, entity):
        return random.choice(self.pseudonyms)