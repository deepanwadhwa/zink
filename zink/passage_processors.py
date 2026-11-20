"""Helpers for detecting entities in sections of a long passage."""

from concurrent.futures import ThreadPoolExecutor

from zink.extractor import _DEFAULT_EXTRACTOR


def _word_end(text, end):
    """Finish the current whitespace-delimited token and its trailing space."""
    while end < len(text) and not text[end - 1].isspace() and not text[end].isspace():
        end += 1
    while end < len(text) and text[end].isspace():
        end += 1
    return end


def chunk_text(text: str, chunk_size: int = 250):
    """Return consecutive, word-preserving (text slice, start offset) pairs.

    Size is a positive soft target in Python characters. A chunk extends to
    finish a word and its trailing whitespace, so even a long word stays intact.
    Punctuation inside names, IDs, and URLs is not treated as a boundary.
    For example, chunk_text("Alice! Bob.", 3) returns [("Alice! ", 0), ("Bob.", 7)].
    Parallel extraction adds context around these non-overlapping core chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    chunks = []
    start = 0
    while start < len(text):
        end = _word_end(text, min(start + chunk_size, len(text)))
        chunks.append((text[start:end], start))
        start = end
    return chunks


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
    """Predict entities with word-preserving chunks and overlapping context.

    All workers use the supplied extractor or the shared default. Each
    returned span is relative to the original passage. Each core chunk gets
    32 to 128 characters of context on each side, extended to whole words.
    Detections must intersect that window's core; duplicate spans keep their
    highest score. Identical windows run once. Context improves boundary
    recognition but cannot guarantee detection of every entity.
    """
    chunks = chunk_text(full_text, chunk_size)
    context = max(32, min(128, chunk_size // 4))
    windows = {}
    for chunk, start in chunks:
        end = start + len(chunk)
        window_start = max(0, start - context)
        while (
            window_start > 0
            and not full_text[window_start].isspace()
            and not full_text[window_start - 1].isspace()
        ):
            window_start -= 1
        window_end = _word_end(full_text, min(end + context, len(full_text)))
        windows.setdefault((window_start, window_end), []).append((start, end))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                extract_entities_for_chunk,
                full_text[start:end],
                start,
                categories,
                extractor=extractor,
            )
            for start, end in windows
        ]
        unique = {}
        for future, cores in zip(futures, windows.values()):
            for entity in future.result():
                if not any(
                    entity["start"] < end and entity["end"] > start
                    for start, end in cores
                ):
                    continue
                key = (entity["start"], entity["end"], entity["label"])
                previous = unique.get(key)
                if previous is None or entity.get("score", 1) > previous.get(
                    "score", 1
                ):
                    unique[key] = entity
        return sorted(
            unique.values(),
            key=lambda entity: (entity["start"], entity["end"], entity["label"]),
        )
