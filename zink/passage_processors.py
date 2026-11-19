"""Helpers for detecting entities in sections of a long passage."""

from concurrent.futures import ThreadPoolExecutor

from zink.extractor import _DEFAULT_EXTRACTOR


def chunk_text(text: str, chunk_size: int = 250):
    """Return consecutive (text slice, start offset) pairs.

    For example, chunk_text("Alice!", 3) returns [("Ali", 0), ("ce!", 3)].
    The chunk size counts Python characters and must be positive. An entity
    that crosses a chunk boundary may be missed by the extraction model.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return [
        (text[start : start + chunk_size], start)
        for start in range(0, len(text), chunk_size)
    ]


def extract_entities_for_chunk(
    chunk_text: str, offset: int, categories=None, *, extractor=None
):
    """Predict entities in one chunk and return their full-passage offsets."""
    if extractor is None:
        extractor = _DEFAULT_EXTRACTOR
    return [
        {**entity, "start": entity["start"] + offset, "end": entity["end"] + offset}
        for entity in extractor.predict(chunk_text, labels=categories)
    ]


def extract_entities_in_parallel(
    full_text: str,
    chunk_size: int = 250,
    max_workers: int = 4,
    categories=None,
    *,
    extractor=None,
):
    """Predict entities in passage chunks and combine them in chunk order.

    All workers use the supplied extractor or the shared default. Each
    returned span is relative to the original passage.
    """
    chunks = chunk_text(full_text, chunk_size)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                extract_entities_for_chunk,
                text,
                offset,
                categories,
                extractor=extractor,
            )
            for text, offset in chunks
        ]
        return [entity for future in futures for entity in future.result()]
