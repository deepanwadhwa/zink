from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
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
        ("é🙂 ABC", 2, [("é🙂 ", 0), ("ABC", 3)]),
        ("abcdef", 3, [("abcdef", 0)]),
        ("Anne-Marie St. John", 3, [("Anne-Marie ", 0), ("St. ", 11), ("John", 15)]),
        ("A\tB\nC", 1, [("A\t", 0), ("B\n", 2), ("C", 4)]),
        ("\t \n", 1, [("\t \n", 0)]),
    ],
)
def test_chunk_text_uses_character_offsets(text, size, expected):
    assert passage_processors.chunk_text(text, size) == expected
    assert "".join(chunk for chunk, _ in expected) == text
    assert all(text[start : start + len(chunk)] == chunk for chunk, start in expected)


@pytest.mark.parametrize("size", [0, -1])
def test_chunk_text_rejects_nonpositive_size(size):
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        passage_processors.chunk_text("Alice", size)


def test_parallel_passage_offsets_and_order_when_last_chunk_finishes_first(monkeypatch):
    last_finished = Event()
    expected_label = ("person",)
    passage = "Ana " + "x " * 38 + "Bob."
    suffix = passage[48:]
    first = _entity(passage, 0, 3, "person")
    last = _entity(suffix, 32, 35, "person", 0.9)

    class Executor(ThreadPoolExecutor):
        def submit(self, fn, text, *args, **kwargs):
            future = super().submit(fn, text, *args, **kwargs)
            if text == suffix:
                future.add_done_callback(lambda _: last_finished.set())
            return future

    class Extractor:
        def predict(self, text, labels):
            assert labels == expected_label
            if text == passage:
                assert last_finished.wait(10), "Last chunk did not finish first"
                return [first, _entity(text, 80, 83, "person", 0.7)]
            assert text == suffix
            return [last]

    monkeypatch.setattr(passage_processors, "ThreadPoolExecutor", Executor)
    assert passage_processors.extract_entities_in_parallel(
        passage, 80, 2, expected_label, extractor=Extractor()
    ) == [first, {**last, "start": 80, "end": 83}]
    assert last["start"] == 32 and last["end"] == 35


@pytest.mark.parametrize(
    "entrypoint", [zink.redact, zink.replace, zink.replace_with_my_data]
)
@pytest.mark.parametrize("size", [1, 7, 11, 16, 20, 32])
@pytest.mark.parametrize(
    "name",
    [
        "Alice Smith", "Anne-Marie Smith", "St. John",
        "J. R. Smith", "李 小明", "Jean—Luc Picard",
    ],
)
def test_chunk_context_preserves_complete_names_and_original_offsets(
    fake_extractor, entrypoint, size, name
):
    text = f"Before {name} arrived."

    def predict(chunk, labels):
        assert tuple(labels) == ("person",)
        return [
            _entity(chunk, match.start(), match.end(), "person")
            for match in re.finditer(re.escape(name), chunk)
        ]

    fake_extractor(predict)
    kwargs = dict(categories=("person",), auto_parallel=True, chunk_size=size)
    if entrypoint is zink.redact:
        kwargs["placeholder"] = "[person]"
    else:
        kwargs["user_replacements"] = {"person": "[person]"}
    result = entrypoint(text, **kwargs)

    assert result.anonymized_text == "Before [person] arrived."
    assert result.features["num_replacements"] == 1
    (detail,) = result.replacements
    if entrypoint is zink.redact:
        assert (detail.start, detail.end, detail.original) == (7, 7 + len(name), name)
    else:
        assert (detail["start"], detail["end"], detail["text"]) == (
            7, 7 + len(name), name
        )


def test_context_only_detection_does_not_escape_its_core():
    passage = "Ana " + "x " * 38 + "Bob."

    class Extractor:
        def predict(self, text, labels):
            # Bob lies entirely outside the first core. Its own window finds
            # nothing, so context alone must not generate a second owner.
            return [_entity(text, 80, 83, "person")] if text == passage else []

    assert passage_processors.extract_entities_in_parallel(
        passage, chunk_size=80, extractor=Extractor()
    ) == []


@pytest.mark.integration
@pytest.mark.parametrize(
    "entrypoint", [zink.redact, zink.replace, zink.replace_with_my_data]
)
@pytest.mark.parametrize("size", [11, 16, 17, 1000])
def test_real_onnx_redacts_name_across_chunk_boundaries(entrypoint, size):
    prefix = "We waited. " * 89 + "Then " if size == 1000 else ""
    text = prefix + "I met Alice Smith yesterday."
    kwargs = dict(categories=("person",), auto_parallel=True, chunk_size=size)
    if entrypoint is zink.redact:
        kwargs["placeholder"] = "[person]"
    else:
        kwargs["user_replacements"] = {"person": "[person]"}
    result = entrypoint(text, **kwargs)

    assert result.anonymized_text == prefix + "I met [person] yesterday."
    assert result.features["num_replacements"] == 1
    (detail,) = result.replacements
    start = len(prefix) + 6
    if entrypoint is zink.redact:
        assert (detail.start, detail.end, detail.original) == (
            start, start + 11, "Alice Smith"
        )
    else:
        assert (detail["start"], detail["end"], detail["text"]) == (
            start, start + 11, "Alice Smith"
        )
