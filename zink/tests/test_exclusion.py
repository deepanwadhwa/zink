import json
import unittest

import pytest

import zink as zn
from zink.pipeline import Pseudonymizer


class TestExclusion(unittest.TestCase):
    @pytest.mark.integration
    def test_basic_exclusion(self):
        text = "I drive a *toyota* car."
        labels = ("car",)
        q = zn.redact(text, labels)
        # "toyota" should be preserved because it's wrapped in *
        self.assertIn("toyota", q.anonymized_text)
        # The * markers should be removed in the final output
        self.assertNotIn("*toyota*", q.anonymized_text)
        self.assertEqual("I drive a toyota car.", q.anonymized_text)

    @pytest.mark.integration
    def test_multiple_exclusions(self):
        text = "I like *apple* and *banana*."
        labels = ("fruit",)  # Assuming fruit is a valid label or just testing mechanism
        # Even if "apple" and "banana" are not entities, the * should be stripped
        q = zn.redact(text, labels)
        self.assertIn("apple", q.anonymized_text)
        self.assertIn("banana", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)

    def test_prep_function(self):
        text = "I drive a rav4, i like toyota cars."
        words = ["toyota"]
        prepared_text = zn.prep(text, words)
        self.assertEqual(prepared_text, "I drive a rav4, i like *toyota* cars.")

    @pytest.mark.integration
    def test_integration_prep_redact(self):
        text = "I drive a rav4, i like toyota cars."
        # rav4 should be redacted, toyota should be kept
        prepared_text = zn.prep(text, ["toyota"])
        labels = ("car",)
        q = zn.redact(prepared_text, labels)

        self.assertNotIn("rav4", q.anonymized_text)
        self.assertIn("toyota", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)

    @pytest.mark.integration
    def test_exclusion_with_punctuation(self):
        text = "I like *toyota*, it is good."
        labels = ("car",)
        q = zn.redact(text, labels)
        self.assertIn("toyota", q.anonymized_text)
        self.assertNotIn("*", q.anonymized_text)
        self.assertEqual("I like toyota, it is good.", q.anonymized_text)

    @pytest.mark.integration
    def test_no_exclusion(self):
        text = "I drive a toyota."
        labels = ("car",)
        q = zn.redact(text, labels)
        self.assertNotIn("toyota", q.anonymized_text)


@pytest.fixture
def detections(monkeypatch):
    """Provide fixed spans and record exactly what each extraction path receives."""
    calls = []

    def install(expected_text, spans):
        def detect(self, text, labels):
            assert text == expected_text
            assert tuple(labels) == ("person",)
            calls.append("single")
            return [
                {
                    "start": start,
                    "end": end,
                    "text": text[start:end],
                    "label": "person",
                    "score": 0.9,
                }
                for start, end in spans
            ]

        def detect_in_chunks(self, text, chunk_size, max_workers, categories):
            assert 0 < chunk_size < len(text)
            entities = detect(self, text, categories)
            calls[-1] = "parallel"
            return entities

        monkeypatch.setattr(Pseudonymizer, "_single_pass_extraction", detect)
        monkeypatch.setattr(Pseudonymizer, "_parallel_extraction", detect_in_chunks)
        return calls

    return install


@pytest.mark.parametrize(
    "words",
    [
        ("Alice", "Alice arrived"),
        ("Alice arrived", "Alice"),
    ],
)
def test_overlapping_protected_phrases_survive_redaction(detections, words):
    text = "Alice arrived."
    detections(text, [(0, 5)])

    prepared = zn.prep(text, words)
    result = zn.redact(prepared, ("person",), use_cache=False)
    assert result.anonymized_text == text
    assert result.replacements == []
    assert result.features["num_replacements"] == 0
    assert prepared == "*Alice arrived*."


@pytest.mark.parametrize(
    ("text", "terms", "prepared"),
    [
        ("Alice Bob Carol", ["alice bob", "BOB CAROL"], "*Alice Bob Carol*"),
        ("a a a", ["a a"], "*a a a*"),
        ("ANN, Annette, Ann", ["ann", "ann"], "*ANN*, Annette, *Ann*"),
        ("Álvaro\nand Zoë", ["álvaro", "zoë"], "*Álvaro*\nand *Zoë*"),
        ("C++ and [QA]", ["c++", "[qa]"], "*C++* and *[QA]*"),
        ("Annette's tea", ["", "Ann", "coffee"], "Annette's tea"),
        ("Alice arrived.", [], "Alice arrived."),
        ("Alice *arrived*.", ["Alice arrived"], "*Alice arrived*."),
        ("*Alice* and Bob", ["Alice", "Bob"], "*Alice* and *Bob*"),
        ("Alice left *", ["Bob"], "Alice left *"),
        ("*Alice* left *", ["Alice"], "*Alice* left *"),
    ],
)
def test_prep_preserves_original_text_and_merges_protection(text, terms, prepared):
    assert zn.prep(text, terms) == prepared
    assert zn.prep(prepared, terms) == prepared


def test_prep_rejects_new_protection_with_an_unmatched_asterisk():
    with pytest.raises(ValueError, match="unmatched asterisk"):
        zn.prep("A note * mentions Alice.", ["Alice"])


def test_redact_preserves_a_lone_literal_asterisk(detections):
    text = "Alice left *"
    detections(text, [(0, 5)])

    result = zn.redact(text, ("person",), use_cache=False)

    assert result.anonymized_text == "person_REDACTED left *"
    assert result.features["num_replacements"] == 1


@pytest.mark.parametrize(
    ("use_cache", "auto_parallel", "expected_route"),
    [
        (False, False, "single"),
        (True, False, "single"),
        (True, True, "parallel"),
    ],
)
def test_only_entities_outside_protection_are_redacted(
    detections,
    use_cache,
    auto_parallel,
    expected_route,
):
    text = "Bob met Alice Smith."
    prepared = zn.prep(text, ["Alice", "Alice Smith"])
    calls = detections(text, [(0, 3), (4, 13), (14, 19)])

    result = zn.redact(
        prepared,
        ("person",),
        use_cache=use_cache,
        auto_parallel=auto_parallel,
        chunk_size=12 if auto_parallel else 100,
    )
    assert result.original_text == "Bob met *Alice Smith*."
    assert result.anonymized_text == "person_REDACTED met Alice Smith."
    assert result.features["num_replacements"] == 1
    assert calls == [expected_route]
    [replacement] = result.replacements
    assert (replacement.original, replacement.start, replacement.end) == ("Bob", 0, 3)


def test_cached_extraction_respects_each_calls_protection(detections):
    text = "Alice met Bob."
    calls = detections(text, [(0, 5), (10, 13)])

    protect_alice = zn.redact(zn.prep(text, ["Alice"]), ("person",))
    protect_bob = zn.redact(zn.prep(text, ["Bob"]), ("person",))

    assert protect_alice.anonymized_text == "Alice met person_REDACTED."
    assert protect_bob.anonymized_text == "person_REDACTED met Bob."
    assert calls == ["single"]


@pytest.mark.parametrize(
    "options",
    [
        {"use_cache": False},
        {"use_cache": True},
        {"auto_parallel": True, "chunk_size": 12},
    ],
    ids=["uncached", "cached", "chunked"],
)
def test_protected_prediction_does_not_hide_an_outside_detection(
    fake_extractor,
    options,
):
    labels = ("person", "full name", "family name")
    calls = []

    def predict(text, categories):
        assert tuple(categories) == labels
        calls.append(text)
        if text == "arrived.":
            return []
        assert text in ("Alice Jones arrived.", "Alice Jones ")
        return [
            {
                "start": start,
                "end": end,
                "text": text[start:end],
                "label": label,
                "score": score,
            }
            for start, end, label, score in [
                (0, 5, "person", 0.95),
                (0, 11, "full name", 0.8),
                (6, 11, "family name", 0.95),
            ]
        ]

    fake_extractor(predict)
    result = zn.redact("*Alice* Jones arrived.", labels, **options)

    assert result.anonymized_text == "Alice family name_REDACTED arrived."
    assert result.features["num_replacements"] == 1
    [replacement] = result.replacements
    assert (replacement.original, replacement.start, replacement.end) == (
        "Jones",
        6,
        11,
    )

    if options.get("use_cache"):
        second = zn.redact("Alice *Jones* arrived.", labels, **options)
        assert second.anonymized_text == "person_REDACTED Jones arrived."
        assert calls == ["Alice Jones arrived."]


def test_redaction_does_not_merge_detections_across_protection(fake_extractor):
    def predict(text, labels):
        assert text == "AnnxBob arrived."
        assert tuple(labels) == ("person",)
        return [
            {
                "start": start,
                "end": end,
                "text": text[start:end],
                "label": "person",
                "score": 0.9,
            }
            for start, end in [(0, 3), (4, 7)]
        ]

    fake_extractor(predict)

    result = zn.redact("Ann*x*Bob arrived.", ("person",), use_cache=False)

    assert result.anonymized_text == "person_REDACTEDxperson_REDACTED arrived."
    assert result.features["num_replacements"] == 2
    assert [replacement.original for replacement in result.replacements] == [
        "Ann",
        "Bob",
    ]


def test_protection_can_cross_a_parallel_chunk_boundary(fake_extractor):
    text = "Bob met Alice Smith."

    def predict(chunk, labels):
        assert tuple(labels) == ("person",)
        spans = {"Bob met Alic": [(0, 3), (8, 12)], "e Smith.": [(0, 7)]}
        return [
            {
                "start": start,
                "end": end,
                "text": chunk[start:end],
                "label": "person",
                "score": 0.9,
            }
            for start, end in spans[chunk]
        ]

    fake_extractor(predict)
    result = zn.redact(
        zn.prep(text, ["Alice", "Alice Smith"]),
        ("person",),
        auto_parallel=True,
        chunk_size=12,
    )

    assert result.anonymized_text == "person_REDACTED met Alice Smith."
    assert [replacement.original for replacement in result.replacements] == ["Bob"]


def test_numbered_redaction_does_not_store_protected_entities(
    detections,
    monkeypatch,
    tmp_path,
):
    text = "Alice arrived. Bob left."
    prepared = zn.prep(text, ["Alice", "Alice arrived"])
    detections(text, [(0, 5), (15, 18)])
    mapping = tmp_path / "mapping.json"
    monkeypatch.setattr("zink.pipeline.get_default_mapping_path", lambda: mapping)

    result = zn.redact(prepared, ("person",), use_cache=False, numbered_entities=True)

    [replacement] = result.replacements
    assert (replacement.original, replacement.start, replacement.end) == ("Bob", 15, 18)
    assert result.anonymized_text == f"Alice arrived. {replacement.pseudonym} left."
    assert set(json.loads(mapping.read_text())["person"]) == {"Bob"}


@pytest.mark.integration
def test_overlapping_protection_with_real_model():
    text = "Alice arrived. Bob left."
    result = zn.redact(zn.prep(text, ["Alice", "Alice arrived"]), ("person",))

    assert result.anonymized_text == "Alice arrived. person_REDACTED left."
    assert [replacement.original for replacement in result.replacements] == ["Bob"]
