# pipeline.py

import warnings
warnings.filterwarnings("ignore")
import random
from collections import defaultdict
from functools import lru_cache
from zink.extractor import _DEFAULT_EXTRACTOR
from zink.merger import EntityMerger
from zink.replacer import EntityReplacer
from zink.result import PseudonymizationResult, ReplacementDetail
from .passage_processors import extract_entities_in_parallel

class Pseudonymizer:
    def __init__(self):
        self.extractor = _DEFAULT_EXTRACTOR
        self.merger = EntityMerger()
        self.replacer = EntityReplacer(use_json_mapping=True)
    
    #
    # 1) SINGLE-PASS: Normal and Cached versions
    #
    def _single_pass_extraction(self, text, categories):
        """Plain extraction & merging (uncached)."""
        raw_ents = self.extractor.predict(text, labels=categories)
        return self.merger.merge(raw_ents, text)

    @lru_cache(maxsize=128)
    def _cached_single_pass_extraction(self, text, categories_tuple):
        """
        Same as _single_pass_extraction, but decorated with lru_cache.
        categories must be passed as a tuple for caching to work.
        """
        raw_ents = self.extractor.predict(text, labels=categories_tuple)
        return self.merger.merge(raw_ents, text)
    
    #
    # 2) PARALLEL: For large texts
    #
    def _parallel_extraction(self, text, chunk_size, max_workers, categories):
        """
        Extract in parallel, then merge globally.
        (Typically not cached, but you can do so if you want.)
        """
        all_ents = extract_entities_in_parallel(
            text, chunk_size=chunk_size, max_workers=max_workers, categories=categories
        )
        all_ents.sort(key=lambda e: e["start"])
        return self.merger.merge(all_ents, text)
    
    #
    # 3) Public Methods
    #
    # def redact(self, text, categories=None, placeholder=None,
    #            use_cache=True, auto_parallel=False, chunk_size=1000, max_workers=4, numbered_entities=False):
    #     """
    #     If auto_parallel=True & text is large, do parallel extraction.
    #     Else do single-pass extraction.
    #     If use_cache=True, we call the cached single-pass method.
    #     """
    #     if len(text) > chunk_size:
    #         auto_parallel = True
    #     if auto_parallel and len(text) > chunk_size:
    #         merged = self._parallel_extraction(text, chunk_size, max_workers, categories)
    #         anonymized = self._do_redact(text, merged, placeholder, numbered_entities=numbered_entities)
    #     else:
    #         # single-pass
    #         if use_cache:
    #             # Convert categories to a tuple for caching
    #             cat_tuple = tuple(categories) if categories else tuple()
    #             merged = self._cached_single_pass_extraction(text, cat_tuple)
    #         else:
    #             merged = self._single_pass_extraction(text, categories)
    #         anonymized = self._do_redact(text, merged, placeholder, numbered_entities=numbered_entities)

    #     return PseudonymizationResult(
    #         original_text=text,
    #         anonymized_text=anonymized,
    #         replacements=merged,
    #         features={"num_replacements": len(merged)},
    #     )

    def redact(self, text, categories=None, placeholder=None, use_cache=True, 
               auto_parallel=False, chunk_size=1000, max_workers=4, numbered_entities=False):
        
        if len(text) > chunk_size and auto_parallel:
            merged = self._parallel_extraction(text, chunk_size, max_workers, categories)
        else:
            if use_cache:
                cat_tuple = tuple(categories) if categories else tuple()
                merged = self._cached_single_pass_extraction(text, cat_tuple)
            else:
                merged = self._single_pass_extraction(text, categories)
        
        anonymized_text, detailed_replacements = self._do_redact(text, merged, placeholder, numbered_entities)

        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=detailed_replacements,
            features={"num_replacements": len(merged)},

        )

    def _do_redact(self, text, merged_entities, placeholder, numbered_entities=False):
        """Replaces entities with placeholders, ensuring consistency for numbered redaction."""
        result_text = text
        replacements_to_apply = []
        detailed_replacements = []

        if numbered_entities:
            # Map (label, text) -> unique_id to ensure consistency
            entity_to_id_map = {}
            # Track used IDs per label to avoid collisions
            used_ids_per_label = defaultdict(set)

            for e in merged_entities:
                label = e['label']
                original_text = e['text']
                entity_key = (label, original_text)

                # If we've seen this entity before, reuse its ID.
                if entity_key in entity_to_id_map:
                    rand_id = entity_to_id_map[entity_key]
                else:
                    # Otherwise, generate a new unique ID and store it.
                    while True:
                        rand_id = str(random.randint(1000, 9999))
                        if rand_id not in used_ids_per_label[label]:
                            used_ids_per_label[label].add(rand_id)
                            entity_to_id_map[entity_key] = rand_id
                            break
                
                pseudonym = f"{label}_{rand_id}_REDACTED"
                replacements_to_apply.append((e['start'], e['end'], pseudonym))
                
                detailed_replacements.append(ReplacementDetail(
                    label=label, original=original_text, pseudonym=pseudonym,
                    start=e['start'], end=e['end'], score=e.get('score', 1.0)
                ))
        else:
            # Standard (non-numbered) redaction
            for e in merged_entities:
                pseudonym = placeholder or f"{e['label']}_REDACTED"
                replacements_to_apply.append((e['start'], e['end'], pseudonym))
                detailed_replacements.append(ReplacementDetail(
                    label=e['label'], original=e['text'], pseudonym=pseudonym,
                    start=e['start'], end=e['end'], score=e.get('score', 1.0)
                ))

        # Apply all replacements from the end to the start to preserve indices.
        for start, end, repl in reversed(replacements_to_apply):
            result_text = result_text[:start] + repl + result_text[end:]
            
        return result_text, detailed_replacements

    def replace(self, text, categories=None, user_replacements=None,
                ensure_consistency=True, use_cache=True,
                auto_parallel=False, chunk_size=1000, max_workers=4):
        """
        Replaces entities with pseudonyms (Faker/JSON).
        If auto_parallel=True & text is large, do parallel extraction.
        Else do single-pass (with optional caching).
        """
        if len(text) > chunk_size:
            auto_parallel = True
        if auto_parallel and len(text) > chunk_size:
            merged = self._parallel_extraction(text, chunk_size, max_workers, categories)
        else:
            # single-pass
            if use_cache:
                cat_tuple = tuple(categories) if categories else tuple()
                merged = self._cached_single_pass_extraction(text, cat_tuple)
            else:
                merged = self._single_pass_extraction(text, categories)

        anonymized_text = self._replace_entities(text, merged, user_replacements, ensure_consistency)
        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=merged,
            features={"num_replacements": len(merged)},
        )

    def _replace_entities(self, text, merged_entities, user_replacements=None, ensure_consistency=True):
        """
        Perform the actual replacements, ensuring consistency if requested.
        """
        if ensure_consistency:
            return self.replacer.replace_entities_ensure_consistency(merged_entities, text, user_replacements)
        else:
            return self.replacer.replace_entities(merged_entities, text, user_replacements)

    def replace_with_my_data(self, text, categories=None, user_replacements=None,
                             ensure_consistency=True,
                             auto_parallel=False, chunk_size=1000, max_workers=4):
        """
        Replaces entities with user-defined data. Typically skip caching, but if you want, you can add it.
        """
        if len(text) > chunk_size:
            auto_parallel = True
        if user_replacements is None or not user_replacements:
            raise ValueError("User replacements must be a non-empty dict.")

        if auto_parallel and len(text) > chunk_size:
            all_entities = self._parallel_extraction(text, chunk_size, max_workers, categories)
        else:
            # Usually user_data changes a lot, so caching might not help, 
            # but you CAN do it if you want. We'll skip here for simplicity.
            all_entities = self._single_pass_extraction(text, categories)

        anonymized_text = self._replace_entities(text, all_entities, user_replacements, ensure_consistency)
        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=all_entities,
            features={"num_replacements": len(all_entities)},
        )
