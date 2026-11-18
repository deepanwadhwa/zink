from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

import zink
from zink import passage_processors
from zink.extractor import EntityExtractor


def punctuation_signature(text):
    """Return the original sequence of punctuation characters."""
    return "".join(char for char in text if char in ".,;:?!")


@pytest.mark.integration
def test_redact():
    original = (Path(__file__).parent / "data" / "sample.txt").read_text(
        encoding="utf-8"
    )
    processed = zink.redact(
        original,
        categories=("person", "date", "location"),
        placeholder="REDACTED",
        use_cache=False,
        auto_parallel=True,
        chunk_size=500,
    )
    assert processed.replacements
    assert punctuation_signature(original) == punctuation_signature(
        processed.anonymized_text
    )


@pytest.mark.integration
def test_replace_with_my_data():
    original = (Path(__file__).parent / "data" / "sample.txt").read_text(
        encoding="utf-8"
    )
    processed = zink.replace_with_my_data(
        original,
        categories=("person", "date", "location"),
        user_replacements={"person": "NAME", "date": "DATE", "location": "PLACE"},
        ensure_consistency=True,
        chunk_size=200,
    )
    assert processed.replacements
    assert punctuation_signature(original) == punctuation_signature(
        processed.anonymized_text
    )


def _entity(text, start, end, label, score=1):
    return {
        "start": start,
        "end": end,
        "label": label,
        "text": text[start:end],
        "score": score,
    }


def test_overlapping_extraction_calls_keep_their_own_text():
    alice_started = Event()
    bob_started = Event()
    alice_masked = Event()
    observed = {}

    class Model:
        def predict_entities(self, text, labels, threshold):
            (label,) = labels
            observed[(label, threshold)] = text
            if threshold == 0.9:
                if label == "person":
                    alice_masked.set()
                return [_entity(text, text.rindex(" ") + 1, len(text), "location")]
            if label == "person":
                alice_started.set()
                assert bob_started.wait(10), "Bob never entered his first pass"
            else:
                bob_started.set()
                assert alice_masked.wait(10), "Alice never entered her second pass"
            return [_entity(text, 0, text.index(" "), label)]

    extractor = EntityExtractor()
    extractor.model = Model()
    with ThreadPoolExecutor(max_workers=2) as executor:
        alice = executor.submit(extractor.predict2, "Alice from Oslo", ["PERSON"])
        assert alice_started.wait(10), "Alice never entered her first pass"
        bob = executor.submit(extractor.predict2, "Bob from Lima", ["NAME"])
        assert alice.result(timeout=15) == [
            _entity("Alice from Oslo", 0, 5, "person"),
            _entity("Alice from Oslo", 11, 15, "location"),
        ]
        assert bob.result(timeout=15) == [
            _entity("Bob from Lima", 0, 3, "name"),
            _entity("Bob from Lima", 9, 13, "location"),
        ]

    assert observed == {
        ("person", 0.5): "Alice from Oslo",
        ("name", 0.5): "Bob from Lima",
        ("person", 0.9): "      from Oslo",
        ("name", 0.9): "    from Lima",
    }


@pytest.mark.parametrize(
    ("method", "first_labels", "other_labels"),
    [
        ("predict2", ("person", "date"), ("location", "name")),
        ("predict_thorough", ("person", "date", "location"), ("name",)),
    ],
)
def test_label_batches_use_independent_masks_and_highest_scoring_spans(
    method, first_labels, other_labels
):
    class Model:
        def predict_entities(self, text, labels, threshold):
            labels = tuple(labels)
            if labels == first_labels:
                if threshold == 0.5:
                    assert text == "Ana in Lima"
                    return [_entity(text, 0, 3, "person", 0.6)]
                assert text == "    in Lima"
                return [_entity(text, 7, 11, "location")]
            assert labels == other_labels
            if threshold == 0.5:
                assert text == "Ana in Lima"
                return [_entity(text, 0, 3, "name", 0.8)]
            assert text == "    in Lima"
            return []

    extractor = EntityExtractor()
    extractor.model = Model()
    predict = getattr(extractor, method)

    assert predict("Ana in Lima", ["PERSON", "Date", "LOCATION", "Name"]) == [
        _entity("Ana in Lima", 0, 3, "name", 0.8),
        _entity("Ana in Lima", 7, 11, "location"),
    ]
    assert predict("Ana in Lima", []) == []


def test_failed_worker_does_not_affect_later_extraction():
    class Model:
        def predict_entities(self, text, labels, threshold):
            if text == "broken":
                raise RuntimeError("inference failed")
            if threshold == 0.5:
                return [_entity(text, 0, len(text), labels[0])]
            assert text.isspace()
            return []

    extractor = EntityExtractor()
    extractor.model = Model()
    with pytest.raises(RuntimeError, match="inference failed"):
        extractor.predict2("broken", ["person"])
    for name in ("Alice", "Bob"):
        assert extractor.predict2(name, ["person"]) == [
            _entity(name, 0, len(name), "person")
        ]


@pytest.mark.parametrize(
    ("text", "size", "expected"),
    [
        ("", 2, []),
        ("é🙂ABC", 2, [("é🙂", 0), ("AB", 2), ("C", 4)]),
        ("abcdef", 3, [("abc", 0), ("def", 3)]),
    ],
)
def test_chunk_text_uses_character_offsets(text, size, expected):
    assert passage_processors.chunk_text(text, size) == expected


@pytest.mark.parametrize("size", [0, -1])
def test_chunk_text_rejects_nonpositive_size(size):
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        passage_processors.chunk_text("Alice", size)


def test_parallel_passage_offsets_and_order_when_last_chunk_finishes_first(monkeypatch):
    last_finished = Event()
    expected_label = ("person",)
    first = _entity("Ana ", 0, 3, "person")
    last = _entity("Bob.", 0, 3, "person")

    class Executor(ThreadPoolExecutor):
        def submit(self, fn, text, *args, **kwargs):
            future = super().submit(fn, text, *args, **kwargs)
            if text == "Bob.":
                future.add_done_callback(lambda _: last_finished.set())
            return future

    class Extractor:
        def predict(self, text, labels):
            assert labels == expected_label
            if text == "Ana ":
                assert last_finished.wait(10), "Last chunk did not finish first"
                return [first]
            assert text == "Bob."
            return [last]

    monkeypatch.setattr(passage_processors, "ThreadPoolExecutor", Executor)
    assert passage_processors.extract_entities_in_parallel(
        "Ana Bob.", 4, 2, expected_label, extractor=Extractor()
    ) == [first, {**last, "start": 4, "end": 7}]
    assert last["start"] == 0 and last["end"] == 3
