# # from .extractor import EntityExtractor
# from .extractor import _DEFAULT_EXTRACTOR
# from .merger import EntityMerger
# from .replacer import EntityReplacer
# from .result import PseudonymizationResult  # Assume you defined this dataclass
# from functools import lru_cache
# import warnings

# warnings.filterwarnings("ignore")

# # Instantiate default components at module load time.

# # _DEFAULT_EXTRACTOR = EntityExtractor()
# _DEFAULT_MERGER = EntityMerger()


# class Pseudonymizer:
#     """
#     Pseudonymizes text by replacing sensitive entities.

#     This class provides three methods to deal with sensitive entities:
#     Redact - replaces sensitive entities with a placeholder. 
#     Replace - replaces sensitive entities with pseudonyms.
#     Replace with your own data - replaces sensitive entities with user-defined pseudonyms.
#     It supports custom user-defined replacements and JSON-based mappings for entity replacement.

#     Parameters:
#         user_replacements (dict, ): A dictionary of user-defined replacements for specific entity labels.
#             If provided, these will override the JSON-based mappings.
#         use_json_mapping (bool, ): If True, use JSON-based mappings for entity replacement.
#             If False, only use user-defined replacements.
#         extractor (EntityExtractor, ): An instance of EntityExtractor for extracting entities from text.
#             If None, a default extractor will be used.
#         merger (EntityMerger, ): An instance of EntityMerger for merging adjacent entities.
#             If None, a default merger will be used.
#         replacer (EntityReplacer, ): An instance of EntityReplacer for replacing entities with pseudonyms.
#             If None, a default replacer will be used.
#         text (str): The input text to be pseudonymized.
#     """

#     def __init__(
#         self, use_json_mapping=True, extractor=None, merger=None, replacer=None
#     ):
#         # 'labels' can be used by the extractor if needed.
#         self.extractor = extractor if extractor is not None else _DEFAULT_EXTRACTOR
#         self.merger = merger if merger is not None else _DEFAULT_MERGER
#         self.replacer = (
#             replacer
#             if replacer is not None
#             else EntityReplacer(use_json_mapping=use_json_mapping)
#         )
#         self.text = ""

#     @lru_cache()
#     def redact(self, text="", categories=None, placeholder=None):
#         """
#         Find and Redact categories in given text.
        
#         Parameters:
#             text (str): The input text.
#             categories (tuple of str, ): Only entities with these labels will be anonymized.
#                 If None, ["person", "date", "location"] are anonymized.
#             placeholder (str, ): The placeholder string to replace the sensitive entities with. 
#                 Example: "REDACTED" or "$$$".
#         """
#         # Validate input parameters.
#         if text is None or text == "":
#             raise ValueError(
#                 "Text must be provided for this method. For example, use `zink.redact(text='your text here')`."
#             )
#         if placeholder is not None and not isinstance(placeholder, str):
#             raise ValueError("Placeholder must be a string.")
#         if not isinstance(text, str):
#             raise ValueError(
#                 "Text must be a string. For example, use `zink.redact(text='your text here')`."
#             )
#         if not text:
#             raise ValueError("Text cannot be empty.")
#         if categories is not None and not isinstance(categories, tuple):
#             raise ValueError(
#                 "Categories must be a tuple of strings. For example, use `zink.redact(text='your text here', categories=('person', 'date'))`."
#             )
#         if categories is not None and not all(isinstance(c, str) for c in categories):
#             raise ValueError("All categories must be strings.")
#         # Step 1: Extract entities and merge adjacent ones.
#         self.text = text
#         entities = self.extractor.predict(self.text, labels=categories)

#         self.merged_entities = self.merger.merge(entities, self.text)

#         # If categories are provided, filter to only include those entities.
#         if categories is not None:
#             categories = [c.lower() for c in categories]
#             self.merged_entities = [
#                 e for e in self.merged_entities if e["label"].lower() in categories
#             ]
#         pseudonymized_text = self.text
#         for ent in self.merged_entities:
#             if placeholder is None:
#                 placeholder_ = f"{ent['label']}_REDACTED"
#             # print(f"Replacing {ent['text']} with {placeholder_}")
#             pseudonymized_text = pseudonymized_text.replace(ent["text"], placeholder_)

#         # Build and return a structured result.
#         return PseudonymizationResult(
#             original_text=self.text,
#             anonymized_text=pseudonymized_text,
#             replacements=self.merged_entities,  # Additional details if needed.
#             features={"num_replacements": len(self.merged_entities)},
#         )

#     @lru_cache()
#     def replace(
#         self, text="", categories=None, user_replacements=None, ensure_consistency=True
#     ):
#         """
#         Find and Replace categories in given text.

#         Parameters:
#             text (str): The input text.
#             categories (tuple of str, ): Only entities with these labels will be anonymized.
#                 If None, all detected entities are anonymized.
#             user_replacements (dict, ): A dictionary of user-defined replacements for specific entity labels.
#                 If provided, these will override the Faker/JSON-based mappings.

#         Returns:
#             PseudonymizationResult: A structured result with original text, pseudonymized text, etc.
#         """
#         # Validate input parameters.
#         if text is None or text == "":
#             raise ValueError(
#                 "Text must be provided for this method. For example, use `replace(text='your text here')`."
#             )
#         if user_replacements is not None:
#             raise ValueError(
#                 "`user_replacements` are not supported in this method. "
#                 "Please use `replace_with_my_data` instead."
#             )
#         if not isinstance(text, str):
#             raise ValueError("Text must be a string.")
#         if not text:
#             raise ValueError("Text cannot be empty.")
#         if categories is not None and not isinstance(categories, tuple):
#             raise ValueError(
#                 "Categories must be a tuple of strings. For example, use `replace(text='your text here', categories=('person', 'date'))`."
#             )
#         if categories is not None and not all(isinstance(c, str) for c in categories):
#             raise ValueError("All categories must be strings.")
#         if ensure_consistency and not isinstance(ensure_consistency, bool):
#             raise ValueError("Ensure consistency must be a boolean.")

#         self.text = text
#         # Step 1: Extract entities and merge adjacent ones.
#         entities = self.extractor.predict(self.text, labels=categories)
#         self.merged_entities = self.merger.merge(entities, self.text)

#         # If categories are provided, filter to only include those entities.
#         if categories is not None:
#             categories = [c.lower() for c in categories]
#             self.merged_entities = [
#                 e for e in self.merged_entities if e["label"].lower() in categories
#             ]

#         # Step 2: Replace entities.
#         if ensure_consistency:
#             # Ensure consistency in replacements.
#             pseudonymized_text = self.replacer.replace_entities_ensure_consistency(
#                 self.merged_entities, self.text, user_replacements
#             )
#         else:
#             # Use the default replacement strategy.
#             pseudonymized_text = self.replacer.replace_entities(
#                 self.merged_entities, self.text, user_replacements
#             )

#         # Build and return a structured result.
#         return PseudonymizationResult(
#             original_text=self.text,
#             anonymized_text=pseudonymized_text,
#             replacements=self.merged_entities,  # Additional details if needed.
#             features={"num_replacements": len(self.merged_entities)},
#         )

#     def replace_with_my_data(
#         self, text="", categories=None, user_replacements=None, ensure_consistency=True
#     ):
#         """
#         Find and Replace categories in given text.

#         Parameters:
#             text (str): The input text.
#             categories (tuple of str, ): Only entities with these labels will be anonymized.
#                 If None, all detected entities are anonymized.
#             user_replacements (dict, ): A dictionary of user-defined replacements for specific entity labels.
#                 If provided, these will override the JSON-based mappings.

#         Returns:
#             PseudonymizationResult: A structured result with original text, pseudonymized text, etc.
#         """
#         if user_replacements is None:
#             raise ValueError(
#                 "User replacements must be provided for this method. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if not isinstance(user_replacements, dict):
#             raise ValueError(
#                 "User replacements must be a dictionary. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if not user_replacements:
#             raise ValueError(
#                 "User replacements dictionary cannot be empty. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if text == "":
#             raise ValueError(
#                 "Text must be provided for this method. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if not isinstance(text, str):
#             raise ValueError(
#                 "Text must be a string. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if not text:
#             raise ValueError(
#                 "Text cannot be empty. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'})`."
#             )
#         if categories is not None and not isinstance(categories, tuple):
#             raise ValueError(
#                 "Categories must be a tuple of strings. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'}, categories=('person', 'date'))`."
#             )
#         if categories is not None and not all(isinstance(c, str) for c in categories):
#             raise ValueError(
#                 "All categories must be strings. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'}, categories=('person', 'date'))`."
#             )
#         if ensure_consistency and not isinstance(ensure_consistency, bool):
#             raise ValueError(
#                 "Ensure consistency must be a boolean. For example, use `replace_with_my_data(text='your text here', user_replacements={'person': 'John'},"
#             )

#         allowed_types = (str, list, tuple)
#         for key, value in user_replacements.items():
#             if not isinstance(value := user_replacements[key], allowed_types):
#                 raise TypeError(
#                     f"Invalid type for key '{key}': expected str, list, or tuple, "
#                     f"got {type(value).__name__} instead."
#                 )

#         self.text = text
#         # Step 1: Extract entities and merge adjacent ones.
#         entities = self.extractor.predict(self.text, labels=categories)
#         self.merged_entities = self.merger.merge(entities, self.text)

#         # If categories are provided, filter to only include those entities.
#         if categories is not None:
#             categories = [c.lower() for c in categories]
#             self.merged_entities = [
#                 e for e in self.merged_entities if e["label"].lower() in categories
#             ]

#         # Step 2: Replace entities.
#         if ensure_consistency:
#             # Ensure consistency in replacements.
#             pseudonymized_text = self.replacer.replace_entities_ensure_consistency(
#                 self.merged_entities, self.text, user_replacements
#             )
#         else:
#             # Use the default replacement strategy.
#             pseudonymized_text = self.replacer.replace_entities(
#                 self.merged_entities, self.text, user_replacements
#             )

#         # Build and return a structured result.
#         return PseudonymizationResult(
#             original_text=self.text,
#             anonymized_text=pseudonymized_text,
#             replacements=self.merged_entities,  # Additional details if needed.
#             features={"num_replacements": len(self.merged_entities)},
#         )


# # For usage enhancement:

# _default_instance = Pseudonymizer()


# @lru_cache()
# def replace(text, categories=None, user_replacements=None, ensure_consistency=True):
#     """
#     Same method as `Pseudonymizer.replace`, but allows for direct usage without instantiating the class.
#     """
#     return _default_instance.replace(
#         text=text,
#         categories=categories,
#         user_replacements=user_replacements,
#         ensure_consistency=ensure_consistency,
#     )


# @lru_cache()
# def redact(text, categories=None, placeholder=None):
#     """
#     Same method as `Pseudonymizer.redact`, but allows for direct usage without instantiating the class.
#     """
#     return _default_instance.redact(
#         text=text, categories=categories, placeholder=placeholder
#     )


# def replace_with_my_data(
#     text, categories=None, user_replacements=None, ensure_consistency=True
# ):
#     """
#     Same method as `Pseudonymizer.replace_with_my_data`, but allows for direct usage without instantiating the class.
#     """
#     return _default_instance.replace_with_my_data(
#         text=text,
#         categories=categories,
#         user_replacements=user_replacements,
#         ensure_consistency=ensure_consistency,
#     )


# # This allows users to call `replace` and `redact` directly without needing to instantiate the class.
# ###############################################


from functools import lru_cache
from zink.extractor import _DEFAULT_EXTRACTOR
from zink.merger import EntityMerger
from zink.replacer import EntityReplacer
from zink.result import PseudonymizationResult
import warnings

warnings.filterwarnings("ignore")

_DEFAULT_MERGER = EntityMerger()

class Pseudonymizer:
    def __init__(self, use_json_mapping=True, extractor=None, merger=None, replacer=None):
        self.extractor = extractor if extractor is not None else _DEFAULT_EXTRACTOR
        self.merger = merger if merger is not None else _DEFAULT_MERGER
        self.replacer = (
            replacer if replacer is not None else EntityReplacer(use_json_mapping=use_json_mapping)
        )
        # Build cached versions of the core functions.
        self._cached_redact = lru_cache(maxsize=128)(self._redact_core)
        self._cached_replace = lru_cache(maxsize=128)(self._replace_core)

    def _redact_core(self, text, categories, placeholder):
        if not text:
            raise ValueError("Text must be provided for redaction.")
        if categories is not None and not isinstance(categories, tuple):
            raise ValueError("Categories must be provided as a tuple of strings.")

        local_text = text
        entities = self.extractor.predict(local_text, labels=categories)
        merged_entities = self.merger.merge(entities, local_text)

        if categories is not None:
            allowed = {c.lower() for c in categories}
            merged_entities = [e for e in merged_entities if e["label"].lower() in allowed]

        result_text = local_text
        for ent in merged_entities:
            replacement = placeholder if placeholder is not None else f"{ent['label']}_REDACTED"
            result_text = result_text.replace(ent["text"], replacement)

        return PseudonymizationResult(
            original_text=local_text,
            anonymized_text=result_text,
            replacements=merged_entities,
            features={"num_replacements": len(merged_entities)},
        )

    def redact(self, text="", categories=None, placeholder=None, use_cache=True):
        """
        Redact sensitive entities from text.
        The new parameter `use_cache` (default True) preserves backward compatibility.
        When set to False, caching is bypassed and the thread‐safe core function is called.
        """
        if use_cache:
            if categories is not None and not isinstance(categories, tuple):
                categories = tuple(categories)
            return self._cached_redact(text, categories, placeholder)
        else:
            return self._redact_core(text, categories, placeholder)

    def _replace_core(self, text, categories, user_replacements, ensure_consistency):
        if not text:
            raise ValueError("Text must be provided for replacement.")
        if categories is not None and not isinstance(categories, tuple):
            raise ValueError("Categories must be provided as a tuple of strings.")

        local_text = text
        entities = self.extractor.predict(local_text, labels=categories)
        merged_entities = self.merger.merge(entities, local_text)

        if categories is not None:
            allowed = {c.lower() for c in categories}
            merged_entities = [e for e in merged_entities if e["label"].lower() in allowed]

        if ensure_consistency:
            result_text = self.replacer.replace_entities_ensure_consistency(
                merged_entities, local_text, user_replacements
            )
        else:
            result_text = self.replacer.replace_entities(
                merged_entities, local_text, user_replacements
            )

        return PseudonymizationResult(
            original_text=local_text,
            anonymized_text=result_text,
            replacements=merged_entities,
            features={"num_replacements": len(merged_entities)},
        )

    def replace(self, text="", categories=None, user_replacements=None, ensure_consistency=True, use_cache=True):
        """
        Replace sensitive entities with pseudonyms.
        The new parameter `use_cache` (default True) preserves backward compatibility.
        When set to False, caching is bypassed and the thread‐safe core function is called.
        """
        if use_cache:
            if categories is not None and not isinstance(categories, tuple):
                categories = tuple(categories)
            return self._cached_replace(text, categories, user_replacements, ensure_consistency)
        else:
            return self._replace_core(text, categories, user_replacements, ensure_consistency)

    def replace_with_my_data(self, text="", categories=None, user_replacements=None, ensure_consistency=True):
        """
        Replace sensitive entities with user-defined data.
        Caching is not applied to this method.
        """
        if user_replacements is None:
            raise ValueError(
                "User replacements must be provided for this method. "
                "For example, use replace_with_my_data(text='...', user_replacements={'person': 'John'})."
            )
        if not isinstance(user_replacements, dict):
            raise ValueError("User replacements must be a dictionary.")
        if not user_replacements:
            raise ValueError("User replacements dictionary cannot be empty.")
        if not text:
            raise ValueError("Text must be provided for this method.")
        if not isinstance(text, str):
            raise ValueError("Text must be a string.")
        if categories is not None and not isinstance(categories, tuple):
            raise ValueError("Categories must be provided as a tuple of strings.")
        if ensure_consistency and not isinstance(ensure_consistency, bool):
            raise ValueError("Ensure consistency must be a boolean.")

        local_text = text
        entities = self.extractor.predict(local_text, labels=categories)
        merged_entities = self.merger.merge(entities, local_text)

        if categories is not None:
            allowed = {c.lower() for c in categories}
            merged_entities = [e for e in merged_entities if e["label"].lower() in allowed]

        if ensure_consistency:
            result_text = self.replacer.replace_entities_ensure_consistency(
                merged_entities, local_text, user_replacements
            )
        else:
            result_text = self.replacer.replace_entities(
                merged_entities, local_text, user_replacements
            )

        return PseudonymizationResult(
            original_text=local_text,
            anonymized_text=result_text,
            replacements=merged_entities,
            features={"num_replacements": len(merged_entities)},
        )

# Create a global instance to preserve cache across calls.
_global_instance = Pseudonymizer()

def redact(text, categories=None, placeholder=None, use_cache=True, use_json_mapping=True, extractor=None, merger=None, replacer=None):
    """
    Module-level convenience function that uses a global instance for caching.
    """
    # If a custom instance is not provided, use the global one.
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.redact(text=text, categories=categories, placeholder=placeholder, use_cache=use_cache)
    else:
        pseudonymizer = Pseudonymizer(use_json_mapping=use_json_mapping, extractor=extractor, merger=merger, replacer=replacer)
        return pseudonymizer.redact(text=text, categories=categories, placeholder=placeholder, use_cache=use_cache)

def replace(text, categories=None, user_replacements=None, ensure_consistency=True, use_cache=True, use_json_mapping=True, extractor=None, merger=None, replacer=None):
    """
    Module-level convenience function that uses a global instance for caching.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.replace(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            use_cache=use_cache
        )
    else:
        pseudonymizer = Pseudonymizer(use_json_mapping=use_json_mapping, extractor=extractor, merger=merger, replacer=replacer)
        return pseudonymizer.replace(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            use_cache=use_cache
        )

def replace_with_my_data(text, categories=None, user_replacements=None, ensure_consistency=True, use_json_mapping=True, extractor=None, merger=None, replacer=None):
    """
    Module-level convenience function. This method always computes fresh results.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency
        )
    else:
        pseudonymizer = Pseudonymizer(use_json_mapping=use_json_mapping, extractor=extractor, merger=merger, replacer=replacer)
        return pseudonymizer.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency
        )
