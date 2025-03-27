# passage_processor.py
import concurrent.futures
from zink.extractor import _DEFAULT_EXTRACTOR

def chunk_text(text: str, chunk_size: int = 250):
    """
    Splits 'text' into slices of length 'chunk_size'.
    Returns a list of (chunk_str, offset) tuples.

    Example:
        If text="Hello world..." length=12000, chunk_size=250,
        you'll get:
          [
            ("Hello world..." up to first 250 chars, offset=0),
            (next 250 chars, offset=250),
            (remaining ~2000 chars, offset=10000)
          ]
    """
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk_str = text[start:end]
        chunks.append((chunk_str, start))
        start = end
    return chunks

def extract_entities_for_chunk(chunk_text: str, offset: int, categories=None):
    """
    Extracts entities from a single chunk using _DEFAULT_EXTRACTOR.
    Adjusts entity 'start'/'end' by 'offset' so they're correct
    relative to the original full text.
    """
    # Run NER on this chunk (optionally respecting 'categories')
    # If categories is None, it will detect all possible entities.
    raw_entities = _DEFAULT_EXTRACTOR.predict(chunk_text, labels=categories)

    # Fix offsets to match the original text
    for ent in raw_entities:
        ent["start"] += offset
        ent["end"]   += offset

    return raw_entities

def extract_entities_in_parallel(
    full_text: str,
    chunk_size: int = 250,
    max_workers: int = 4,
    categories=None
):
    """
    Splits the text into chunks, and extracts entities from each chunk in parallel
    (using ThreadPoolExecutor). Returns a single combined list of entity dicts,
    with offsets corrected to match the full text.

    1) chunk_text(...)
    2) spawn parallel workers -> extract_entities_for_chunk(...)
    3) gather partial results & combine
    4) returns a list of entity dicts, each with 'start', 'end', 'label', 'text', etc.
    """
    chunks = chunk_text(full_text, chunk_size)
    all_entities = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for chunk_str, offset in chunks:
            # Pass categories along if desired
            futures.append(executor.submit(
                extract_entities_for_chunk,
                chunk_text=chunk_str,
                offset=offset,
                categories=categories
            ))

        for future in concurrent.futures.as_completed(futures):
            partial_entities = future.result()
            all_entities.extend(partial_entities)

    return all_entities
