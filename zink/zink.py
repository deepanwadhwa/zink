# zink.py
from .pipeline import Pseudonymizer
import functools
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
    numbered_entities=False  # Default to False for compatibility
):
    """
    Module-level convenience function that uses a global instance for caching.
    If 'auto_parallel' is True and len(text) > chunk_size, concurrency-based pipeline is used.
    Otherwise single-pass logic is used.
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
            numbered_entities=numbered_entities
        )
    else:
        # Create a fresh instance
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer
        )
        return pseudonymizer.redact(
            text=text,
            categories=categories,
            placeholder=placeholder,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers,
            numbered_entities= numbered_entities
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
    max_workers=4
):
    """
    Module-level convenience function that uses a global instance for caching.
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
            max_workers=max_workers
        )
    else:
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer
        )
        return pseudonymizer.replace(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            use_cache=use_cache,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers
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
    max_workers=4
):
    """
    Module-level convenience function. 
    Typically 'replace_with_my_data' does NOT rely on caching,
    but we might still want concurrency for large texts if 'auto_parallel' is True.
    """
    if extractor is None and merger is None and replacer is None and use_json_mapping:
        return _global_instance.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers
        )
    else:
        pseudonymizer = Pseudonymizer(
            use_json_mapping=use_json_mapping,
            extractor=extractor,
            merger=merger,
            replacer=replacer
        )
        return pseudonymizer.replace_with_my_data(
            text=text,
            categories=categories,
            user_replacements=user_replacements,
            ensure_consistency=ensure_consistency,
            auto_parallel=auto_parallel,
            chunk_size=chunk_size,
            max_workers=max_workers
        )

def shield(target_arg, labels=None, **zink_kwargs):
    """
    A decorator that provides a full anonymization/re-identification 
    "shield" for a function call.

    It anonymizes a specific input argument, calls the decorated function,
    and then automatically re-identifies the function's string output.

    Args:
        target_arg (str or int): The name (str) or position (int) of the 
            input argument to anonymize.
        labels (tuple or list): The entity labels to anonymize. Required.
        **zink_kwargs: Additional keyword arguments for the underlying
            zn.redact function.
    """
    if labels is None:
        raise ValueError("The 'labels' argument is required for the shield decorator.")

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
                original_text,
                categories=labels,
                numbered_entities=True,
                **zink_kwargs
            )
            anonymized_text = result_obj.anonymized_text
            reid_map = {item.pseudonym: item.original for item in result_obj.replacements}

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
                return anonymized_response # Return non-strings as-is

            reidentified_response = anonymized_response
            for pseudonym, original in reid_map.items():
                reidentified_response = reidentified_response.replace(pseudonym, original)

            # 6. Return the final, re-identified result
            return reidentified_response
        return wrapper
    return decorator