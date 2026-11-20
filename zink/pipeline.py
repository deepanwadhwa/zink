# pipeline.py
import random
import json
import os
from collections import defaultdict
from functools import lru_cache
from threading import RLock
from zink.extractor import _DEFAULT_EXTRACTOR
from zink.merger import EntityMerger
from zink.replacer import EntityReplacer
from zink.result import PseudonymizationResult, ReplacementDetail
from zink.utils.paths import get_default_mapping_path
from zink.utils.mapping import save_mapping
from .passage_processors import extract_entities_in_parallel

_MAPPING_LOCK = RLock()


class Pseudonymizer:
    """Coordinate extraction, span merging, and text transformation.

    Args:
        use_json_mapping (bool): Enable bundled replacement fallback values.
        extractor: Optional object providing ``predict2`` and ``predict``.
        merger: Optional object providing ``merge(entities, text)``.
        replacer: Optional ``EntityReplacer``-compatible object.
    """

    def __init__(
        self, use_json_mapping=True, extractor=None, merger=None, replacer=None
    ):
        self.extractor = extractor if extractor is not None else _DEFAULT_EXTRACTOR
        self.merger = merger if merger is not None else EntityMerger()
        self.replacer = (
            replacer
            if replacer is not None
            else EntityReplacer(use_json_mapping=use_json_mapping)
        )

    def _single_pass_extraction(self, text, categories):
        """Return raw detections before protection filtering or span merging."""
        return self.extractor.predict2(text, labels=categories)

    @lru_cache(maxsize=128)
    def _cached_single_pass_extraction(self, text, categories_tuple):
        """
        Cache raw detections; each call applies its own protection and merging.
        """

        return self._single_pass_extraction(text, categories_tuple)

    def _parallel_extraction(self, text, chunk_size, max_workers, categories):
        """
        Return raw chunk detections in original-text coordinates without caching.
        """
        all_ents = extract_entities_in_parallel(
            text,
            chunk_size=chunk_size,
            max_workers=max_workers,
            categories=categories,
            extractor=self.extractor,
        )
        all_ents.sort(key=lambda e: e["start"])
        return all_ents

    def _merge_for_redaction(self, entities, text, protected_spans):
        """Merge detections within unprotected regions, never across a marker.

        A broad detection touching protection is discarded before merging, so
        it cannot hide a separate detection outside the protected interval.
        """
        if not protected_spans:
            return self.merger.merge(entities, text)

        merged = []
        region_start = 0
        for protected_start, protected_end in [
            *protected_spans,
            (len(text), len(text)),
        ]:
            region_entities = [
                entity
                for entity in entities
                if region_start <= entity["start"] < entity["end"] <= protected_start
            ]
            if region_entities:
                region_merged = self.merger.merge(region_entities, text)
                if any(
                    not region_start
                    <= entity["start"]
                    < entity["end"]
                    <= protected_start
                    for entity in region_merged
                ):
                    raise ValueError("Merged entity crosses a protected boundary")
                merged.extend(region_merged)
            region_start = protected_end
        return merged

    def redact(
        self,
        text,
        categories=None,
        placeholder=None,
        use_cache=True,
        auto_parallel=False,
        chunk_size=1000,
        max_workers=4,
        numbered_entities=False,
    ):
        """Redact detected spans after filtering overlaps with protected text.

        See :func:`zink.redact` for the arguments and result fields. Numbered
        mapping updates are serialized across threads in this process.
        """
        # 1. Parse exclusion markers
        clean_text, protected_spans = self._parse_exclusions(text)

        # 2. Run extraction on CLEAN text
        if len(clean_text) > chunk_size and auto_parallel:
            merged = self._parallel_extraction(
                clean_text, chunk_size, max_workers, categories
            )
        else:
            if use_cache:
                cat_tuple = tuple(categories) if categories is not None else None
                merged = self._cached_single_pass_extraction(clean_text, cat_tuple)
            else:
                merged = self._single_pass_extraction(clean_text, categories)

        # Filter raw predictions before merging, and keep protected gaps intact.
        filtered_entities = self._merge_for_redaction(
            merged, clean_text, protected_spans
        )

        # 4. Redact the clean text
        with _MAPPING_LOCK:
            anonymized_text, detailed_replacements = self._do_redact(
                clean_text, filtered_entities, placeholder, numbered_entities
            )

        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=detailed_replacements,
            features={"num_replacements": len(filtered_entities)},
        )

    def _parse_exclusions(self, text):
        """
        Parses text for *word* patterns.
        Returns:
            clean_text: Text with * removed.
            protected_spans: List of (start, end) tuples in clean_text coordinates that should be protected.
        """
        clean_text = ""
        protected_spans = []

        i = 0
        n = len(text)
        clean_idx = 0

        while i < n:
            if text[i] == "*":
                # Pair consecutive markers; keep an unmatched trailing * literal.
                closing_idx = text.find("*", i + 1)
                if closing_idx != -1:
                    # Found a pair
                    span_content = text[i + 1 : closing_idx]
                    start_span = clean_idx
                    clean_text += span_content
                    clean_idx += len(span_content)
                    end_span = clean_idx
                    if start_span < end_span:
                        protected_spans.append((start_span, end_span))

                    i = closing_idx + 1
                else:
                    # No closing *, treat as literal
                    clean_text += text[i]
                    clean_idx += 1
                    i += 1
            else:
                clean_text += text[i]
                clean_idx += 1
                i += 1

        return clean_text, protected_spans

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
            available_ids_per_label = {}

            # Load existing mapping from default path
            mapping_file = get_default_mapping_path()
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, "r") as f:
                        loaded_mapping = json.load(f)
                        # Reconstruct entity_to_id_map and used_ids_per_label
                        # Expected format: {"label": {"original_text": "id"}}
                        for label, entries in loaded_mapping.items():
                            for original_text, ent_id in entries.items():
                                entity_to_id_map[(label, original_text)] = ent_id
                                used_ids_per_label[label].add(ent_id)
                except Exception as e:
                    print(f"Warning: Failed to load mapping file {mapping_file}: {e}")

            for e in merged_entities:
                label = e["label"]
                original_text = e["text"]
                entity_key = (label, original_text)

                # If we've seen this entity before, reuse its ID.
                if entity_key in entity_to_id_map:
                    rand_id = entity_to_id_map[entity_key]
                else:
                    # Build each label's remaining pool once. Random retries
                    # cannot terminate when the four-digit ID space is full.
                    if label not in available_ids_per_label:
                        available_ids_per_label[label] = [
                            str(value)
                            for value in range(1000, 10000)
                            if str(value) not in used_ids_per_label[label]
                        ]
                    available = available_ids_per_label[label]
                    if not available:
                        raise ValueError(
                            f"Numbered IDs exhausted for label {label!r}: all "
                            "9,000 IDs (1000-9999) are in use. Existing mappings "
                            "can still be reused."
                        )
                    index = random.randrange(len(available))
                    rand_id = available[index]
                    available[index] = available[-1]
                    available.pop()
                    used_ids_per_label[label].add(rand_id)
                    entity_to_id_map[entity_key] = rand_id

                pseudonym = f"{label}_{rand_id}_REDACTED"
                replacements_to_apply.append((e["start"], e["end"], pseudonym))

                detailed_replacements.append(
                    ReplacementDetail(
                        label=label,
                        original=original_text,
                        pseudonym=pseudonym,
                        start=e["start"],
                        end=e["end"],
                        score=e.get("score", 1.0),
                    )
                )

            # Save updated mapping
            try:
                # Convert back to serializable format: {"label": {"original_text": "id"}}
                serializable_mapping = defaultdict(dict)
                for (label, original_text), ent_id in entity_to_id_map.items():
                    serializable_mapping[label][original_text] = ent_id

                save_mapping(mapping_file, serializable_mapping)
            except Exception as e:
                print(f"Warning: Failed to save mapping file {mapping_file}: {e}")

        else:
            # Standard (non-numbered) redaction
            for e in merged_entities:
                pseudonym = placeholder or f"{e['label']}_REDACTED"
                replacements_to_apply.append((e["start"], e["end"], pseudonym))
                detailed_replacements.append(
                    ReplacementDetail(
                        label=e["label"],
                        original=e["text"],
                        pseudonym=pseudonym,
                        start=e["start"],
                        end=e["end"],
                        score=e.get("score", 1.0),
                    )
                )

        # Apply all replacements from the end to the start to preserve indices.
        for start, end, repl in reversed(replacements_to_apply):
            result_text = result_text[:start] + repl + result_text[end:]

        return result_text, detailed_replacements

    def replace(
        self,
        text,
        categories=None,
        user_replacements=None,
        ensure_consistency=True,
        use_cache=True,
        auto_parallel=False,
        chunk_size=1000,
        max_workers=4,
    ):
        """
        Replace detected spans using a per-call consistent or independent mapping.

        See :func:`zink.replace`. Long text is chunked when it exceeds
        ``chunk_size``. Returned entity dictionaries are private to this result.
        """
        if len(text) > chunk_size:
            auto_parallel = True
        if auto_parallel and len(text) > chunk_size:
            merged = self._parallel_extraction(
                text, chunk_size, max_workers, categories
            )
        else:
            # single-pass
            if use_cache:
                cat_tuple = tuple(categories) if categories is not None else None
                merged = self._cached_single_pass_extraction(text, cat_tuple)
            else:
                merged = self._single_pass_extraction(text, categories)

        merged = [dict(entity) for entity in self.merger.merge(merged, text)]
        anonymized_text = self._replace_entities(
            text, merged, user_replacements, ensure_consistency
        )
        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=merged,
            features={"num_replacements": len(merged)},
        )

    def _replace_entities(
        self, text, merged_entities, user_replacements=None, ensure_consistency=True
    ):
        """
        Perform the actual replacements, ensuring consistency if requested.
        """
        if ensure_consistency:
            return self.replacer.replace_entities_ensure_consistency(
                merged_entities, text, user_replacements
            )
        else:
            return self.replacer.replace_entities(
                merged_entities, text, user_replacements
            )

    def replace_with_my_data(
        self,
        text,
        categories=None,
        user_replacements=None,
        ensure_consistency=True,
        auto_parallel=False,
        chunk_size=1000,
        max_workers=4,
    ):
        """
        Replace detected spans with required user data, without caching extraction.

        See :func:`zink.replace_with_my_data` for the arguments and result fields.
        """
        if len(text) > chunk_size:
            auto_parallel = True
        if user_replacements is None or not user_replacements:
            raise ValueError("User replacements must be a non-empty dict.")

        if auto_parallel and len(text) > chunk_size:
            all_entities = self._parallel_extraction(
                text, chunk_size, max_workers, categories
            )
        else:
            all_entities = self._single_pass_extraction(text, categories)

        all_entities = [
            dict(entity) for entity in self.merger.merge(all_entities, text)
        ]
        anonymized_text = self._replace_entities(
            text, all_entities, user_replacements, ensure_consistency
        )
        return PseudonymizationResult(
            original_text=text,
            anonymized_text=anonymized_text,
            replacements=all_entities,
            features={"num_replacements": len(all_entities)},
        )
