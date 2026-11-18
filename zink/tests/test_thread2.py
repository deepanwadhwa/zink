from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

import zink
from zink.tests.test_thread import punctuation_signature


SAMPLE_TEXT = (
    "Alice was born on 1990-01-01 in Paris. "
    "Bob moved to New York in 2010. "
    "Charlie went to London in 2005."
)
LABELS = ("person", "date", "location")


@pytest.mark.integration
def test_redact_preserves_structure():
    processed = zink.redact(SAMPLE_TEXT, categories=LABELS, placeholder="REDACTED")
    assert processed.replacements
    assert punctuation_signature(SAMPLE_TEXT) == punctuation_signature(
        processed.anonymized_text
    )


@pytest.mark.integration
def test_replace_preserves_structure():
    processed = zink.replace(SAMPLE_TEXT, categories=LABELS)
    assert processed.replacements
    assert punctuation_signature(SAMPLE_TEXT) == punctuation_signature(
        processed.anonymized_text
    )


@pytest.mark.integration
def test_replace_with_my_data_preserves_structure():
    replacements = {"person": "NAME", "date": "DATE", "location": "PLACE"}
    processed = zink.replace_with_my_data(
        SAMPLE_TEXT, categories=LABELS, user_replacements=replacements
    )
    assert processed.replacements
    assert punctuation_signature(SAMPLE_TEXT) == punctuation_signature(
        processed.anonymized_text
    )


@pytest.mark.integration
def test_real_model_shared_by_concurrent_redaction_calls():
    inputs = ("Alice lives in Paris.", "Bob lives in London.")
    labels = ("person", "location")
    start = Barrier(2)

    def redact(text):
        start.wait(timeout=10)
        return zink.redact(text, categories=labels, use_cache=False)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(redact, text) for text in inputs]
        results = [future.result(timeout=45) for future in futures]

    for expected, text, result in zip(
        [("Alice", "Paris"), ("Bob", "London")], inputs, results
    ):
        assert result.original_text == text
        assert tuple(detail.original for detail in result.replacements) == expected
        assert result.anonymized_text == "person_REDACTED lives in location_REDACTED."
        for detail in result.replacements:
            assert text[detail.start : detail.end] == detail.original


@pytest.mark.parametrize("use_cache", [False, True])
def test_overlapping_public_replacement_calls_keep_their_own_mappings(
    monkeypatch, use_cache
):
    from threading import Event

    from zink.zink import _global_instance

    text = "Alice arrived."
    alice_mapping_read = Event()
    bob_finished = Event()

    class Extractor:
        model = object()

        def predict2(self, text, labels):
            assert text == "Alice arrived."
            assert labels == ("person",)
            return [
                {"start": 0, "end": 5, "label": "person", "text": "Alice", "score": 1}
            ]

    class DelayedMapping(dict):
        def items(self):
            yield from super().items()
            alice_mapping_read.set()
            assert bob_finished.wait(10), "Second replacement never finished"

    def transform(mapping):
        return zink.replace(
            text,
            categories=("person",),
            user_replacements=mapping,
            use_cache=use_cache,
        )

    monkeypatch.setattr(_global_instance, "extractor", Extractor())
    _global_instance._cached_single_pass_extraction.cache_clear()
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            alice = executor.submit(transform, DelayedMapping(person="Ana"))
            assert alice_mapping_read.wait(10), (
                "First replacement never read its mapping"
            )
            try:
                bob = executor.submit(transform, {"person": "Bea"}).result(timeout=15)
            finally:
                bob_finished.set()
            alice = alice.result(timeout=15)
    finally:
        _global_instance._cached_single_pass_extraction.cache_clear()

    assert alice.anonymized_text == "Ana arrived."
    assert bob.anonymized_text == "Bea arrived."
    assert alice.replacements[0]["source"] == bob.replacements[0]["source"] == "user"
    alice.replacements[0]["source"] = "changed"
    assert bob.replacements[0]["source"] == "user"
