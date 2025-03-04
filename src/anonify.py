from extractor import EntityExtractor
from merger import EntityMerger
from replacer import EntityReplacer
from result import PseudonymizationResult  # Assume you defined this dataclass
import warnings
warnings.filterwarnings("ignore")
from functools import lru_cache
# Instantiate default components at module load time.


_DEFAULT_EXTRACTOR = EntityExtractor()
_DEFAULT_MERGER = EntityMerger()


class Pseudonymizer:
    """
    A class for pseudonymizing text by replacing sensitive entities with non-sensitive placeholders.
    This class provides methods to extract entities, merge adjacent entities, and replace them with pseudonyms.
    It supports custom user-defined replacements and JSON-based mappings for entity replacement.
    Parameters:
        user_replacements (dict, optional): A dictionary of user-defined replacements for specific entity labels.
            If provided, these will override the JSON-based mappings.
        use_json_mapping (bool, optional): If True, use JSON-based mappings for entity replacement.
            If False, only use user-defined replacements.
        extractor (EntityExtractor, optional): An instance of EntityExtractor for extracting entities from text.
            If None, a default extractor will be used.
        merger (EntityMerger, optional): An instance of EntityMerger for merging adjacent entities.
            If None, a default merger will be used.
        replacer (EntityReplacer, optional): An instance of EntityReplacer for replacing entities with pseudonyms.
            If None, a default replacer will be used.
        text (str): The input text to be pseudonymized.
    """
    def __init__(self, use_json_mapping=True,
                 extractor=None, merger=None, replacer=None):
        # 'labels' can be used by the extractor if needed.
        self.extractor = extractor if extractor is not None else _DEFAULT_EXTRACTOR
        self.merger = merger if merger is not None else _DEFAULT_MERGER
        self.replacer = (replacer if replacer is not None 
                         else EntityReplacer(use_json_mapping=use_json_mapping))
        self.text = ""
    
    @lru_cache()
    def redact(self, text = "",categories=None,placeholder=None):
        """
        Find and Redact categories in given text.
        Parameters:
            text (str): The input text.
            categories (tuple of str, optional): Only entities with these labels will be anonymized.
                If None, ["person", "date", "location"] are anonymized.
        """
        # Step 1: Extract entities and merge adjacent ones.
        self.text = text
        entities = self.extractor.predict(self.text, labels = categories)

        self.merged_entities = self.merger.merge(entities, self.text)
        
        # If categories are provided, filter to only include those entities.
        if categories is not None:
            categories = [c.lower() for c in categories]
            self.merged_entities = [e for e in self.merged_entities if e['label'].lower() in categories]
        pseudonymized_text = self.text
        for ent in self.merged_entities:
            if placeholder is None:
                placeholder_ = f"{ent['label']}_REDACTED"
            #print(f"Replacing {ent['text']} with {placeholder_}")
            pseudonymized_text = pseudonymized_text.replace(ent['text'], placeholder_)
        
        # Build and return a structured result.
        return PseudonymizationResult(
            original_text=self.text,
            anonymized_text=pseudonymized_text,
            replacements=self.merged_entities,  # Additional details if needed.
            features={"num_replacements": len(self.merged_entities)}
        )
    
    @lru_cache()
    def replace(self, text = "",categories=None, user_replacements=None, ensure_consistency=True):
        """
        Find and Replace categories in given text.
        
        Parameters:
            text (str): The input text.
            categories (tuple of str, optional): Only entities with these labels will be anonymized.
                If None, all detected entities are anonymized.
            user_replacements (dict, optional): A dictionary of user-defined replacements for specific entity labels.
                If provided, these will override the JSON-based mappings.
        
        Returns:
            PseudonymizationResult: A structured result with original text, pseudonymized text, etc.
        """
        self.text = text
        # Step 1: Extract entities and merge adjacent ones.
        entities = self.extractor.predict(self.text, labels = categories)
        self.merged_entities = self.merger.merge(entities, self.text)
        
        # If categories are provided, filter to only include those entities.
        if categories is not None:
            categories = [c.lower() for c in categories]
            self.merged_entities = [e for e in self.merged_entities if e['label'].lower() in categories]
        
        # Step 2: Replace entities.
        if ensure_consistency:
            # Ensure consistency in replacements.
            pseudonymized_text = self.replacer.replace_entities_ensure_consistency(self.merged_entities, self.text, user_replacements)
        else:
            # Use the default replacement strategy.
            pseudonymized_text = self.replacer.replace_entities(self.merged_entities, self.text, user_replacements)
        
        # Build and return a structured result.
        return PseudonymizationResult(
            original_text=self.text,
            anonymized_text=pseudonymized_text,
            replacements=self.merged_entities,  # Additional details if needed.
            features={"num_replacements": len(self.merged_entities)}
        )



# For usage enhancement:

_default_instance = Pseudonymizer()

@lru_cache()
def replace(text, categories=None, user_replacements=None, ensure_consistency=True):
    return _default_instance.replace(
        text=text,
        categories=categories,
        user_replacements=user_replacements,
        ensure_consistency=ensure_consistency
    )

@lru_cache()
def redact(text, categories=None, placeholder=None):
    return _default_instance.redact(
        text=text,
        categories=categories,
        placeholder=placeholder
    )
# This allows users to call `replace` and `redact` directly without needing to instantiate the class.