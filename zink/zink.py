# zink.py
from .pipeline import Pseudonymizer

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
    max_workers=4
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
            max_workers=max_workers
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
            max_workers=max_workers
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
