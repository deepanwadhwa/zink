import random

from .rfakerjson import FakerOrJsonReplacementStrategy


class EntityReplacer:
    """Apply pseudonyms at detected spans in the original input."""

    def __init__(self, use_json_mapping=False):
        self.use_json_mapping = use_json_mapping

    def replace_entities_ensure_consistency(
        self, entities, text, user_replacements=None
    ):
        """Reuse one pseudonym per label and exact source string within a call.

        Entities must be ordered by start offset and must not overlap. The first
        detected occurrence of a label/source pair chooses its replacement. Each
        entity's dictionary receives the source of the applied replacement.
        A missing or unchanged replacement falls back to `<label>_REDACTED`.
        """
        return self._replace(entities, text, user_replacements, ensure_consistency=True)

    def replace_entities(self, entities, text, user_replacements=None):
        """Replace detected spans, choosing the pseudonym independently for each.

        The span requirements, source metadata and redaction fallback match
        :meth:`replace_entities_ensure_consistency`.
        """
        return self._replace(
            entities, text, user_replacements, ensure_consistency=False
        )

    def _replace(self, entities, text, user_replacements, *, ensure_consistency):
        user_replacements = {
            label.lower(): value for label, value in (user_replacements or {}).items()
        }
        replacements = {}
        parts = []
        previous_end = 0
        for entity in entities:
            original = entity["text"]
            key = (entity["label"].lower(), original)
            if ensure_consistency and key in replacements:
                replacement, source = replacements[key]
            else:
                replacement, source = self._choose_replacement(
                    entity, user_replacements
                )
                if ensure_consistency:
                    replacements[key] = replacement, source

            parts.extend((text[previous_end : entity["start"]], replacement))
            entity["source"] = source
            previous_end = entity["end"]

        parts.append(text[previous_end:])
        return "".join(parts)

    def _choose_replacement(self, entity, user_replacements):
        label = entity["label"].lower()
        if label in user_replacements:
            fixed = user_replacements[label]
            replacement = random.choice(fixed) if isinstance(fixed, list) else fixed
            source = "user"
        else:
            replacement, source = FakerOrJsonReplacementStrategy(
                label, self.use_json_mapping
            ).replace(entity)

        if replacement is None or replacement == entity["text"]:
            return f"{label}_REDACTED", "redaction"
        return replacement, source
