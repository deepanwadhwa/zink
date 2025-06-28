import random
from .rfakerjson import FakerOrJsonReplacementStrategy


class EntityReplacer:
    def __init__(self, use_json_mapping=False):
        """
        Initialize the EntityReplacer.
        Parameters:
            use_json_mapping: If True, JSON mapping is used as a fallback when Faker cannot produce a value.

        """
        self.use_json_mapping = use_json_mapping

    def replace_entities_ensure_consistency(
        self, entities, text, user_replacements=None
    ):
        """
        Replace entities in the text with pseudonyms, ensuring consistent replacements.

        Parameters:
            entities (list of dict): A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
            text (str): The original text.
            user_replacements (dict, ): A dictionary of user-defined replacements for specific entity labels.
                If provided, these will override the JSON-based mappings.
        Returns:
            str: The text with entities replaced by pseudonyms.
        """
        # Initialize user_replacements as an empty dictionary.
        self.user_replacements = {}
        if user_replacements:
            for label, replacement in user_replacements.items():
                self.user_replacements[label.lower()] = replacement

        replacements = {}
        for ent in entities:
            if ent["text"] not in replacements:
                label = ent["label"].lower()
                if label in self.user_replacements:
                    fixed = self.user_replacements[label]
                    replacement = (
                        random.choice(fixed) if isinstance(fixed, list) else fixed
                    )
                    source = "user"
                else:
                    replacement, source = FakerOrJsonReplacementStrategy(
                        label, self.use_json_mapping
                    ).replace(ent)
                ent["source"] = source  # Record the source in the entity.
                replacements[ent["text"]] = replacement

        for key, value in replacements.items():
            text = text.replace(key, value)
        return text

    def replace_entities(self, entities, text, user_replacements=None):
        """
        Replace entities in the text with pseudonyms, with randomized replacements.
        
        Parameters:
            entities (list of dict): A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
            text (str): The original text.
            user_replacements (dict, ): A dictionary of user-defined replacements for specific entity labels.
                If provided, these will override the JSON-based mappings.
        
        Returns:
            str: The text with entities replaced by pseudonyms.
        """
        self.user_replacements = {}
        if user_replacements:
            for label, replacement in user_replacements.items():
                self.user_replacements[label.lower()] = replacement

        new_text = ""
        last_index = 0
        for entity in entities:
            new_text += text[last_index : entity["start"]]
            label = entity["label"].lower()
            if label in self.user_replacements:
                fixed = self.user_replacements[label]
                replacement = random.choice(fixed) if isinstance(fixed, list) else fixed
                source = "user"
            else:
                replacement, source = FakerOrJsonReplacementStrategy(
                    label, self.use_json_mapping
                ).replace(entity)
            if replacement is None or replacement == entity["text"]:
                replacement = label+"_REDACTED"
                source = "redaction"
            entity["source"] = source  # Record the source in the entity.
            new_text += replacement
            last_index = entity["end"]
        new_text += text[last_index:]
        return new_text
