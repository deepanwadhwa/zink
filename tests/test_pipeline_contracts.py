import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest

import zink


def _entity(text, start, end, label="person"):
    return {
        "start": start,
        "end": end,
        "label": label,
        "text": text[start:end],
        "score": 0.95,
    }


@pytest.mark.parametrize("entrypoint", [zink.replace, zink.replace_with_my_data])
@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_public_replacement_honors_custom_components(entrypoint, ensure_consistency):
    text = "Alice and Bob."
    categories = ("person",)

    def extract(passage, labels):
        assert passage == text
        assert labels == categories
        return [_entity(passage, 0, 5), _entity(passage, 10, 13)]

    def keep_only_bob(entities, passage):
        assert passage == text
        assert [entity["text"] for entity in entities] == ["Alice", "Bob"]
        return [entities[1]]

    class Replacer:
        def replace_entities_ensure_consistency(self, entities, passage, values):
            return self.apply(entities, passage, values, "consistent")

        def replace_entities(self, entities, passage, values):
            return self.apply(entities, passage, values, "independent")

        def apply(self, entities, passage, values, source):
            (entity,) = entities
            assert entity["text"] == "Bob"
            entity["source"] = source
            value = values[entity["label"]]
            return (
                passage[: entity["start"]]
                + f"{value}-{source}"
                + passage[entity["end"] :]
            )

    source = "consistent" if ensure_consistency else "independent"
    result = entrypoint(
        text,
        categories=categories,
        user_replacements={"person": "Name"},
        ensure_consistency=ensure_consistency,
        extractor=SimpleNamespace(predict2=extract),
        merger=SimpleNamespace(merge=keep_only_bob),
        replacer=Replacer(),
    )

    assert result.original_text == text
    assert result.anonymized_text == f"Alice and Name-{source}."
    assert result.replacements == [{**_entity(text, 10, 13), "source": source}]
    assert result.features["num_replacements"] == 1


@pytest.mark.parametrize("entrypoint", [zink.replace, zink.replace_with_my_data])
@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_label_scope_reaches_custom_replacer_only_when_consistency_is_enabled(
    entrypoint, ensure_consistency
):
    from zink.replacer import EntityReplacer

    text = "Jordan met Jordan."
    calls = []

    def extract(passage, labels):
        return [_entity(passage, 0, 6, "person"), _entity(passage, 11, 17, "location")]

    class Replacer:
        def replace_entities_ensure_consistency(
            self, entities, passage, values, *, consistency_scope
        ):
            calls.append(consistency_scope)
            return EntityReplacer().replace_entities_ensure_consistency(
                entities, passage, values, consistency_scope=consistency_scope
            )

        def replace_entities(self, entities, passage, values):
            calls.append("independent")
            return EntityReplacer().replace_entities(entities, passage, values)

    result = entrypoint(
        text,
        categories=("person", "location"),
        user_replacements={"person": "Alice", "location": "Venice"},
        ensure_consistency=ensure_consistency,
        consistency_scope="label",
        extractor=SimpleNamespace(predict2=extract),
        replacer=Replacer(),
    )
    assert result.anonymized_text == "Alice met Venice."
    assert calls == ["label" if ensure_consistency else "independent"]


@pytest.mark.parametrize("entrypoint", [zink.replace, zink.replace_with_my_data])
def test_existing_positional_replacement_arguments_keep_their_meaning(entrypoint):
    text = "Jordan met Jordan."

    def extract(passage, labels):
        return [_entity(passage, 0, 6, "person"), _entity(passage, 11, 17, "location")]

    values = {"person": "Alice", "location": "Venice"}
    extractor = SimpleNamespace(predict2=extract)
    if entrypoint is zink.replace:
        args = (
            text,
            ("person", "location"),
            values,
            True,
            True,
            True,
            extractor,
            None,
            None,
            False,
            1000,
            4,
        )
    else:
        args = (
            text,
            ("person", "location"),
            values,
            True,
            True,
            extractor,
            None,
            None,
            False,
            1000,
            4,
        )
    assert entrypoint(*args).anonymized_text == "Alice met Alice."
    assert (
        entrypoint(*args, consistency_scope="label").anonymized_text
        == "Alice met Venice."
    )


def test_parallel_public_redaction_honors_custom_extractor_and_merger():
    text = "Ana Bob."
    calls = []

    def extract(chunk, labels):
        assert labels == ("person",)
        assert chunk == text
        calls.append(chunk)
        return [_entity(chunk, 0, 3), _entity(chunk, 4, 7)]

    def keep_only_bob(entities, passage):
        assert passage == text
        assert entities == [_entity(text, 0, 3), _entity(text, 4, 7)]
        return [entities[1]]

    result = zink.redact(
        text,
        categories=("person",),
        placeholder="[person]",
        auto_parallel=True,
        chunk_size=4,
        max_workers=2,
        extractor=SimpleNamespace(predict=extract),
        merger=SimpleNamespace(merge=keep_only_bob),
    )

    assert result.anonymized_text == "Ana [person]."
    assert calls == [text]  # Identical context windows are inferred only once.
    assert result.features["num_replacements"] == 1
    (detail,) = result.replacements
    assert (detail.original, detail.start, detail.end, detail.pseudonym) == (
        "Bob",
        4,
        7,
        "[person]",
    )


@pytest.mark.parametrize("use_cache", [True, False])
def test_default_and_empty_categories_remain_distinct(fake_extractor, use_cache):
    text = "Alice waited."
    seen = []

    def extract(passage, labels):
        seen.append(labels)
        if labels is None:
            return [_entity(passage, 0, 5)]
        assert not labels
        return []

    fake_extractor(extract)

    for _ in range(2):
        default = zink.redact(text, use_cache=use_cache)
        empty = zink.redact(text, categories=[], use_cache=use_cache)
        assert default.anonymized_text == "person_REDACTED waited."
        assert empty.anonymized_text == text
        assert empty.replacements == []
    assert seen == ([None, ()] if use_cache else [None, [], None, []])


def test_mutating_returned_replacement_details_does_not_poison_cached_results(
    fake_extractor,
):
    text = "Alice waited."
    detections = _entity(text, 0, 5)
    calls = []

    def extract(passage, labels):
        calls.append((passage, labels))
        return [detections]

    fake_extractor(extract)
    result = zink.replace(text, ["person"], user_replacements={"person": "Ana"})
    (details,) = result.replacements
    details.update(start=6, end=12, label="location", text="waited", source="changed")
    result.replacements.clear()

    again = zink.replace(text, ("person",), user_replacements={"person": "Bea"})
    assert again.anonymized_text == "Bea waited."
    assert again.replacements == [{**detections, "source": "user"}]
    assert detections == _entity(text, 0, 5)
    assert calls == [(text, ("person",))]


def test_concurrent_numbered_redaction_preserves_ids_in_one_process(fake_extractor):
    def extract(text, labels):
        return [_entity(text, 0, len(text) - 1)]

    fake_extractor(extract)
    prior = zink.redact("Dee.", numbered_entities=True).replacements[0].pseudonym

    input_names = ["Ann", "Ben", "Ann", "Cam"]
    start = Barrier(len(input_names))

    def redact(name):
        start.wait(timeout=10)
        result = zink.redact(f"{name}.", numbered_entities=True)
        (detail,) = result.replacements
        assert detail.original == name
        assert result.anonymized_text == f"{detail.pseudonym}."
        return detail.pseudonym

    with ThreadPoolExecutor(max_workers=len(input_names)) as pool:
        results = [pool.submit(redact, name) for name in input_names]
        ids = [future.result(timeout=15) for future in results]

    assert ids[0] == ids[2]
    assert len(set(ids + [prior])) == 4
    mapping = json.loads(Path(zink.where_mapping_file()).read_text(encoding="utf-8"))
    expected = {"Dee": prior, **dict(zip(input_names, ids))}
    assert {
        name: f"person_{ident}_REDACTED" for name, ident in mapping["person"].items()
    } == expected


@pytest.mark.parametrize("reverse_order", [False, True])
def test_default_merger_covers_crossing_and_nested_detections(
    fake_extractor, reverse_order
):
    text = "Alice Doe, then Bob."
    outer = {**_entity(text, 0, 5), "score": 0.8}
    nested = {**_entity(text, 0, 3, "name"), "score": 0.9}
    crossing = {**_entity(text, 4, 9, "person"), "score": 0.85}
    bob = _entity(text, 16, 19)
    predictions = [outer, nested, crossing, bob]

    def extract(passage, labels):
        assert passage == text
        return predictions[::-1] if reverse_order else predictions

    fake_extractor(extract)
    result = zink.replace(text, user_replacements={"name": "A", "person": "B"})

    assert result.anonymized_text == "A, then B."
    assert result.replacements == [
        {**nested, "end": 9, "text": "Alice Doe", "source": "user"},
        {**bob, "source": "user"},
    ]
    assert nested["text"] == "Ali"
    assert all("source" not in prediction for prediction in predictions)


@pytest.mark.parametrize("reverse_order", [False, True])
def test_merger_overlap_priority_and_adjacency_metadata(reverse_order):
    from zink.merger import EntityMerger

    text = "A B C ; D E"
    shorter = {**_entity(text, 0, 1, "aaa"), "score": 0.9}
    longest_later_label = {**_entity(text, 0, 3, "zzz"), "score": 0.9}
    longest_first_label = {
        **_entity(text, 0, 3, "person"),
        "score": 0.9,
        "extra": "first",
    }
    adjacent = {**_entity(text, 4, 5), "score": 0.7}
    separated = _entity(text, 8, 9)
    other_label = _entity(text, 10, 11, "letter")
    predictions = [
        shorter,
        longest_later_label,
        longest_first_label,
        adjacent,
        separated,
        other_label,
    ]
    original_predictions = [entity.copy() for entity in predictions]

    result = EntityMerger().merge(
        predictions[::-1] if reverse_order else predictions, text
    )

    assert result == [
        {**longest_first_label, "end": 5, "text": "A B C", "score": pytest.approx(0.8)},
        separated,
        other_label,
    ]
    assert predictions == original_predictions
    assert all(
        entity is not separated and entity is not other_label for entity in result
    )


@pytest.mark.parametrize(("start", "end"), [(-1, 3), (1, 1), (2, 1), (0, 4), (0.5, 1)])
def test_invalid_detection_offsets_raise_before_rendering(fake_extractor, start, end):
    fake_extractor(
        lambda text, labels: [
            {"start": start, "end": end, "label": "person", "text": "Ana", "score": 1}
        ]
    )
    with pytest.raises(ValueError, match="Entity span"):
        zink.redact("Ana")
