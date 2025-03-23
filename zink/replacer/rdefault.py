from .base import ReplacementStrategy


class DefaultReplacementStrategy(ReplacementStrategy):
    """
    Default replacement strategy that replaces all entities with a generic
    placeholder. This is used when no replacement strategy is available.
    """
    def replace(self, entity):
        return "[REDACTED]"
