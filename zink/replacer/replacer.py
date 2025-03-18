
# import random
# from .json_mapping import JsonMappingReplacementStrategy
# from .rdefault import DefaultReplacementStrategy
# from .rfakerjson import FakerOrJsonReplacementStrategy


# class EntityReplacer:
#     def __init__(self, use_json_mapping=False):
#         """
#         user_replacements: Optional dict mapping label -> fixed replacement string or list.
#                            These override any JSON mapping.
#         use_json_mapping: Boolean flag. If True, then for any entity not overridden by
#                           user_replacements, the JSON mapping is used.
#         """
        
#         self.use_json_mapping = use_json_mapping

#     def replace_entities_ensure_consistency(self, entities, text, user_replacements=None):
#         """
#         Replace entities in the text with pseudonyms.
#         Parameters:
#             entities (list of dict): A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
#             text (str): The original text.
#             user_replacements (dict, optional): A dictionary of user-defined replacements for specific entity labels.
#                 If provided, these will override the JSON-based mappings.
#         Returns:
#             str: The text with entities replaced by pseudonyms.
#         1. If user_replacements is provided, it overrides any JSON mapping.
#         2. If use_json_mapping is True, JSON mapping is used for entities not in user_replacements.
#         3. Otherwise, DefaultReplacementStrategy is used.
#         4. If no entities are found, the original text is returned.
#         """
#         self.user_replacements = {}
#         if user_replacements:
#             for label, replacement in user_replacements.items():
#                 self.user_replacements[label.lower()] = replacement

#         new_text = ""
#         last_index = 0
#         replacements = {}
#         for ent in entities:
#             if ent['text'] not in replacements.keys():
#                 label = ent['label'].lower()
#                 if label in self.user_replacements:
#                     fixed = self.user_replacements[label]
#                     if isinstance(fixed, list):
#                         replacement = random.choice(fixed)
#                     else:
#                         replacement = fixed
#                 elif self.use_json_mapping:
#                     replacement = JsonMappingReplacementStrategy(label).replace(ent)
#                 else:
#                     replacement = DefaultReplacementStrategy().replace(ent)
#                 replacements[ent['text']] = replacement
#         for key, value in replacements.items():
#             text = text.replace(key, value)
#         return text
    
#     def replace_entities(self, entities, text, user_replacements=None):
#         """
#         Replace entities in the text with pseudonyms.
#         Parameters:
#             entities (list of dict): A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
#             text (str): The original text.
#             user_replacements (dict, optional): A dictionary of user-defined replacements for specific entity labels.
#                 If provided, these will override the JSON-based mappings.
#         Returns:
#             str: The text with entities replaced by pseudonyms.
#         1. If user_replacements is provided, it overrides any JSON mapping.
#         2. Otherwise, DefaultReplacementStrategy is used.
#         3. If no entities are found, the original text is returned.
#         """
#         self.user_replacements = {}
#         if user_replacements:
#             for label, replacement in user_replacements.items():
#                 self.user_replacements[label.lower()] = replacement

#         new_text = ""
#         last_index = 0
        
#         for entity in entities:
#             #if entity not in replacement_found
#             new_text += text[last_index:entity['start']]
#             label = entity['label'].lower()
#             replacement = None

#             # Priority: user replacement > JSON mapping (if enabled) > default
#             if label in self.user_replacements:
#                 fixed = self.user_replacements[label]
#                 if isinstance(fixed, list):
#                     replacement = random.choice(fixed)
#                 else:
#                     replacement = fixed
#             elif self.use_json_mapping:
#                 replacement = JsonMappingReplacementStrategy(label).replace(entity)
#             else:
#                 replacement = DefaultReplacementStrategy().replace(entity)
#             new_text += replacement
#             last_index = entity['end']
#         new_text += text[last_index:]
#         return new_text
# replacer.py (modified excerpt)
# replacer.py (modified excerpt)
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

    def replace_entities_ensure_consistency(self, entities, text, user_replacements=None):
        """
        Replace entities in the text with pseudonyms, ensuring consistent replacements.
        
        Parameters:
            entities (list of dict): A list of dictionaries, each containing 'start', 'end', 'label', and 'text'.
            text (str): The original text.
            user_replacements (dict, optional): A dictionary of user-defined replacements for specific entity labels.
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
            if ent['text'] not in replacements:
                label = ent['label'].lower()
                if label in self.user_replacements:
                    fixed = self.user_replacements[label]
                    replacement = random.choice(fixed) if isinstance(fixed, list) else fixed
                    source = "user"
                else:
                    replacement, source = FakerOrJsonReplacementStrategy(label, self.use_json_mapping).replace(ent)
                ent["source"] = source  # Record the source in the entity.
                replacements[ent['text']] = replacement

        for key, value in replacements.items():
            text = text.replace(key, value)
        return text

    def replace_entities(self, entities, text, user_replacements=None):
        self.user_replacements = {}
        if user_replacements:
            for label, replacement in user_replacements.items():
                self.user_replacements[label.lower()] = replacement

        new_text = ""
        last_index = 0
        for entity in entities:
            new_text += text[last_index:entity['start']]
            label = entity['label'].lower()
            if label in self.user_replacements:
                fixed = self.user_replacements[label]
                replacement = random.choice(fixed) if isinstance(fixed, list) else fixed
                source = "user"
            else:
                replacement, source = FakerOrJsonReplacementStrategy(label, self.use_json_mapping).replace(entity)
            entity["source"] = source  # Record the source in the entity.
            new_text += replacement
            last_index = entity['end']
        new_text += text[last_index:]
        return new_text

