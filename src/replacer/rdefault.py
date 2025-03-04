from .base import ReplacementStrategy

class DefaultReplacementStrategy(ReplacementStrategy):
    def replace(self, entity):
        return "[REDACTED]"