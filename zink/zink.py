# zink.py
from .pipeline import Pseudonymizer
import functools
import os
from zink.utils.paths import get_default_mapping_path

# Create a global instance to preserve cache across calls.
_global_instance = Pseudonymizer()


def redact(
    text,
    categories=None,
    placeholder=None,
    use_cache=True,
    use_json_mapping=True,
    extractor=None,
    merger=None,
    replacer=None,
    # Below are concurrency-related or advanced parameters:
    auto_parallel=False,
    chunk_size=1000,
    max_workers=4,
    numbered_entities=False,  # Default to False for compatibility
):
    """Detect and redact entities in text.

    Args:
        text (str): Input text. ``*protected text*`` is excluded from redaction;
            the asterisks are removed from the result.
        categories (sequence of str, optional): Entity labels. Defaults to
            ``person``, ``date`` and ``location`` in the extractor.
        placeholder (str, optional): One replacement for every detected span.
            Defaults to ``<label>_REDACTED``.
        use_cache (bool): Reuse extraction results for identical text and labels.
        use_json_mapping (bool): Select the default JSON-backed replacer when
            constructing the pipeline. Has no effect on redaction output.
        extractor: Optional extractor providing ``predict2`` for single text and
            ``predict`` for chunks. Offsets must refer to the supplied text.
        merger: Optional object providing ``merge(entities, text)``.
        replacer: Optional ``EntityReplacer``-compatible replacement component.
        auto_parallel (bool): Extract long text in chunks when it exceeds
            ``chunk_size``. Defaults to false.
        chunk_size (int): Soft chunk target in characters. Chunks finish whole
            words and add overlapping context for detection across boundaries.
        max_workers (int): Maximum worker threads for parallel extraction.
        numbered_entities (bool): Use stable numbered placeholders persisted in
            ``~/.zink/mapping.json``. This file contains original sensitive text.
            Each label supports 9,000 distinct source strings. A new string
            raises ``ValueError`` when that label's IDs are exhausted;
            existing mappings can still be reused across calls and sessions.

    Returns:
        zink.result.PseudonymizationResult: Redacted text, detected spans and
        the number of replacements.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        # Use global instance + built-in concurrency if desired
        return _global_instance.redact(
            text=text,
            categories=categories,
            placeholder=placeholder,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
            numbered_entities=numbered_entities,
        )
    else:
        # Create a fresh instance
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer,
        )
        return pseudonymizer.redact(
            text=text,
            categories=categories,
            placeholder=placeholder,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
            numbered_entities=numbered_entities,
        )


def replace(
    text,
    categories=None,
    user_replacements=None,
    ensure_consistency=True,
    use_cache=True,
    use_json_mapping=True,
    extractor=None,
    merger=None,
    replacer=None,
    auto_parallel=False,
    chunk_size=1000,
    max_workers=4,
):
    """Replace detected entities with synthetic or user supplied values.

    Args:
        text (str): Input text.
        categories (sequence of str, optional): Entity labels to detect.
        user_replacements (dict, optional): Mapping from label to a fixed string
            or list of candidate strings. Keys are case insensitive.
        ensure_consistency (bool): Reuse one replacement for repeated source
            strings with the same label in this call. Different labels have
            independent replacements. Defaults to true.
        use_cache (bool): Reuse extraction for identical text and labels.
        use_json_mapping (bool): Use bundled replacement values as a fallback.
        extractor: Optional extractor providing ``predict2`` and ``predict``.
        merger: Optional object providing ``merge(entities, text)``.
        replacer: Optional ``EntityReplacer``-compatible replacement component.
        auto_parallel (bool): Request chunked extraction for long text. Text
            longer than ``chunk_size`` is chunked regardless of this setting.
        chunk_size (int): Soft chunk target in characters. Chunks finish whole
            words and add overlapping context for detection across boundaries.
        max_workers (int): Maximum worker threads for parallel extraction.

    Returns:
        zink.result.PseudonymizationResult: Result with transformed text.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.replace(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
        )
    else:
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer,
        )
        return pseudonymizer.replace(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
        )


def replace_with_my_data(
    text,
    categories=None,
    user_replacements=None,
    ensure_consistency=True,
    use_json_mapping=True,
    extractor=None,
    merger=None,
    replacer=None,
    # Usually we don't cache user-defined replacements, but if you want concurrency, add it:
    auto_parallel=False,
    chunk_size=1000,
    max_workers=4,
):
    """Replace detected entities using a required custom label mapping.

    Args:
        text (str): Input text.
        categories (sequence of str, optional): Entity labels to detect.
        user_replacements (dict): Nonempty mapping from label to a fixed string
            or list of candidate strings. Unmapped labels use normal fallback.
        ensure_consistency (bool): Reuse one replacement for repeated source
            strings with the same label in this call. Different labels have
            independent replacements.
        use_json_mapping (bool): Use bundled values for unmapped labels.
        extractor: Optional extractor providing ``predict2`` and ``predict``.
        merger: Optional object providing ``merge(entities, text)``.
        replacer: Optional ``EntityReplacer``-compatible replacement component.
        auto_parallel (bool): Request chunked extraction for long text.
        chunk_size (int): Soft chunk target in characters. Longer text is chunked
            with whole words and overlapping context across boundaries.
        max_workers (int): Maximum worker threads for parallel extraction.

    Returns:
        zink.result.PseudonymizationResult: Result with transformed text.

    Raises:
        ValueError: If ``user_replacements`` is empty or omitted.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
        )
    else:
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer,
        )
        return pseudonymizer.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
        )


def shield(target_arg, labels=None, **zink_kwargs):
    """Decorate a function to redact one argument and restore its string output.

    Args:
        target_arg (str or int): Keyword name or zero-based positional index
            of the text argument. Pass the argument in the selected form when
            calling the decorated function.
        labels (sequence of str): Required entity labels.
        **zink_kwargs: Additional options passed to :func:`redact`. Do not
            pass ``numbered_entities``; the decorator sets it to true.

    Returns:
        callable: Wrapped function. String responses have placeholders replaced
        with their original values; other response types pass through unchanged.

    Notes:
        The function sees the redacted argument, but its returned string is
        re-identified and may contain sensitive data. Numbered redaction also
        stores the source values in the local mapping file.
    """
    if labels is None:
        raise ValueError("The 'labels' argument is required for the shield decorator.")
    if isinstance(target_arg, int) and target_arg < 0:
        raise ValueError("The target argument index must be non-negative.")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Find and extract the original text from the function's arguments
            original_text = None
            is_kwarg = False
            if isinstance(target_arg, str) and target_arg in kwargs:
                original_text = kwargs[target_arg]
                is_kwarg = True
            elif isinstance(target_arg, int) and target_arg < len(args):
                original_text = args[target_arg]
            else:
                raise ValueError(f"Argument '{target_arg}' not found in function call.")

            if not isinstance(original_text, str):
                raise TypeError(f"Target argument '{target_arg}' must be a string.")

            # 2. Anonymize the input and build the re-identification map.
            #    `numbered_entities` must be True for re-identification to work.
            result_obj = redact(
                original_text, categories=labels, numbered_entities=True, **zink_kwargs
            )
            anonymized_text = result_obj.anonymized_text
            reid_map = {
                item.pseudonym: item.original for item in result_obj.replacements
            }

            # 3. Create new arguments for the wrapped function, with the text anonymized
            if is_kwarg:
                kwargs[target_arg] = anonymized_text
            else:
                args = list(args)
                args[target_arg] = anonymized_text
                args = tuple(args)

            # 4. Call the wrapped function (e.g., the LLM) with the safe, anonymized data
            anonymized_response = func(*args, **kwargs)

            # 5. Re-identify the placeholders in the function's output string
            if not isinstance(anonymized_response, str):
                return anonymized_response  # Return non-strings as-is

            reidentified_response = anonymized_response
            for pseudonym, original in reid_map.items():
                reidentified_response = reidentified_response.replace(
                    pseudonym, original
                )

            # 6. Return the final, re-identified result
            return reidentified_response

        return wrapper

    return decorator


def where_mapping_file():
    """Return the path to the numbered entity mapping file.

    The call creates the ``~/.zink`` directory if needed. The mapping file
    contains original entity text, so treat it as sensitive data.
    """
    return get_default_mapping_path()


def refresh_mapping_file():
    """Delete the numbered entity mapping file if it exists.

    Existing placeholders cannot be resolved after the file is deleted.
    """
    path = get_default_mapping_path()
    if os.path.exists(path):
        os.remove(path)


def prep(text, words):
    """Mark whole words or phrases to exclude from :func:`redact`.

    Args:
        text (str): Input text.
        words (sequence of str): Case-insensitive terms to protect. Empty
            terms are ignored. Matches cannot touch a word character on
            either side.

    Returns:
        str: Input with matching spans marked by paired asterisks. Protection
        includes existing marked spans and merges overlapping or touching spans.
        Original casing is preserved.

    Raises:
        ValueError: If an unmatched asterisk prevents adding new markers.
    """
    if not words:
        return text

    import re

    clean_text, existing_spans = _global_instance._parse_exclusions(text)
    new_spans = []
    for word in set(words):
        if word:
            # Use lookahead so a phrase can overlap another occurrence of itself.
            pattern = rf"(?=(?<!\w)({re.escape(word)})(?!\w))"
            new_spans.extend(
                match.span(1)
                for match in re.finditer(pattern, clean_text, re.IGNORECASE)
            )
    if not new_spans:
        return text

    merged_spans = []
    for start, end in sorted(existing_spans + new_spans):
        if merged_spans and start <= merged_spans[-1][1]:
            previous_start, previous_end = merged_spans[-1]
            merged_spans[-1] = (previous_start, max(previous_end, end))
        else:
            merged_spans.append((start, end))
    if merged_spans == existing_spans:
        return text
    if "*" in clean_text:
        raise ValueError(
            "Cannot add protection markers to text with an unmatched asterisk."
        )

    parts = []
    cursor = 0
    for start, end in merged_spans:
        parts.extend((clean_text[cursor:start], "*", clean_text[start:end], "*"))
        cursor = end
    parts.append(clean_text[cursor:])
    return "".join(parts)
