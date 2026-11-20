import json
import re
from pathlib import Path

import pytest

import zink as zn
from zink.utils.paths import get_default_mapping_path


@pytest.fixture
def mapping_file(tmp_path):
    return tmp_path / "mapping.json"


@pytest.mark.integration
def test_persistent_mapping_consistency(mapping_file):
    text = "My name is Alice and I work at Google."
    labels = ["person", "company"]

    first = zn.redact(text, categories=labels, numbered_entities=True)
    assert "person_" in first.anonymized_text
    assert "company_" in first.anonymized_text
    mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert "Alice" in mapping["person"]
    assert "Google" in mapping["company"]

    repeated = zn.redact(text, categories=labels, numbered_entities=True)
    assert first.anonymized_text == repeated.anonymized_text

    changed = zn.redact(
        "Alice is a great engineer at Google.",
        categories=labels,
        numbered_entities=True,
    )
    alice_id = mapping["person"]["Alice"]
    google_id = mapping["company"]["Google"]
    assert f"person_{alice_id}_REDACTED" in changed.anonymized_text
    assert f"company_{google_id}_REDACTED" in changed.anonymized_text


@pytest.mark.integration
def test_persistent_mapping_new_entities(mapping_file):
    zn.redact("Alice is here.", categories=["person"], numbered_entities=True)
    before = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert set(before["person"]) == {"Alice"}

    zn.redact("Bob is here.", categories=["person"], numbered_entities=True)
    after = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert set(after["person"]) == {"Alice", "Bob"}
    assert after["person"]["Alice"] == before["person"]["Alice"]
    assert after["person"]["Bob"] != after["person"]["Alice"]


@pytest.mark.integration
def test_shield_with_implicit_mapping(mapping_file):
    @zn.shield(target_arg="prompt", labels=("person",))
    def echo(prompt):
        return prompt

    assert echo(prompt="Alice is calling.") == "Alice is calling."
    before = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert "Alice" in before["person"]

    assert echo(prompt="Alice again.") == "Alice again."
    after = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert before["person"]["Alice"] == after["person"]["Alice"]


@pytest.mark.integration
def test_refresh_mapping_file(mapping_file):
    zn.redact("Alice is here.", categories=["person"], numbered_entities=True)
    assert mapping_file.is_file()

    zn.refresh_mapping_file()

    assert not mapping_file.exists()


def test_mapping_reset_is_idempotent(mapping_file):
    mapping_file.write_text('{"person": {"Alice": "1234"}}', encoding="utf-8")

    zn.refresh_mapping_file()
    zn.refresh_mapping_file()

    assert not mapping_file.exists()


def test_where_mapping_file(monkeypatch, tmp_path):
    monkeypatch.setattr("zink.zink.get_default_mapping_path", get_default_mapping_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    path = Path(zn.where_mapping_file())

    assert path == tmp_path / ".zink" / "mapping.json"
    assert path.parent.is_dir()
    assert not path.exists()


def test_fresh_pipeline_reuses_numbered_mapping(fake_extractor, mapping_file):
    def predict(text, labels):
        assert tuple(labels) == ("person",)
        entities = []
        for name in ("Alice", "Bob"):
            if name in text:
                start = text.index(name)
                entities.append(
                    {
                        "start": start,
                        "end": start + len(name),
                        "text": name,
                        "label": "person",
                        "score": 0.9,
                    }
                )
        return entities

    original_pipeline = fake_extractor(predict)
    first = zn.redact("Alice arrived.", ("person",), numbered_entities=True)
    new_pipeline = fake_extractor(predict)
    assert new_pipeline is not original_pipeline
    second = zn.redact("Alice called Bob.", ("person",), numbered_entities=True)

    alice, bob = second.replacements
    assert alice.pseudonym == first.replacements[0].pseudonym
    assert bob.pseudonym != alice.pseudonym
    stored = json.loads(mapping_file.read_text(encoding="utf-8"))
    assert set(stored["person"]) == {"Alice", "Bob"}


@pytest.fixture
def numbered_predictor(fake_extractor):
    def predict(text, labels):
        return [
            {
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "label": labels[0],
                "score": 1.0,
            }
            for match in re.finditer(r"\w+", text)
        ]

    fake_extractor(predict)


def _occupied_person_ids(mapping_file, stop=10000):
    mapping = {"person": {f"entity{i}": str(i) for i in range(1000, stop)}}
    mapping_file.write_text(json.dumps(mapping), encoding="utf-8")
    return mapping


def test_numbered_exhaustion_raises_without_random_retries(
    numbered_predictor, mapping_file, monkeypatch
):
    _occupied_person_ids(mapping_file)
    before = mapping_file.read_bytes()

    def unexpected_retry(*args):
        pytest.fail("Exhausted allocation must terminate before drawing random IDs")

    # Bound the old implementation too: a regression fails rather than hangs.
    monkeypatch.setattr("zink.pipeline.random.randint", unexpected_retry)
    monkeypatch.setattr("zink.pipeline.random.randrange", unexpected_retry)
    with pytest.raises(ValueError, match="exhausted.*person.*9,000"):
        zn.redact("Alice", ("person",), numbered_entities=True)

    assert mapping_file.read_bytes() == before
    # An error releases the mapping lock and leaves old IDs usable.
    reused = zn.redact("entity1000", ("person",), numbered_entities=True)
    assert reused.anonymized_text == "person_1000_REDACTED"


def test_full_numbered_label_does_not_exhaust_other_labels(
    numbered_predictor, mapping_file
):
    before = _occupied_person_ids(mapping_file)
    result = zn.redact("Venice", ("location",), numbered_entities=True)
    stored = json.loads(mapping_file.read_text(encoding="utf-8"))

    assert stored["person"] == before["person"]
    assert set(stored["location"]) == {"Venice"}
    assert result.anonymized_text == (
        f"location_{stored['location']['Venice']}_REDACTED"
    )


def test_last_numbered_id_is_available_without_collision_retries(
    numbered_predictor, mapping_file
):
    _occupied_person_ids(mapping_file, stop=9999)
    first = zn.redact("Alice", ("person",), numbered_entities=True)
    assert first.anonymized_text == "person_9999_REDACTED"
    assert zn.redact(
        "Alice", ("person",), numbered_entities=True
    ).anonymized_text == first.anonymized_text
    before = mapping_file.read_bytes()

    with pytest.raises(ValueError, match="exhausted"):
        zn.redact("Bob", ("person",), numbered_entities=True)
    assert mapping_file.read_bytes() == before


def test_numbered_exhaustion_does_not_partially_persist_a_request(
    numbered_predictor, mapping_file
):
    _occupied_person_ids(mapping_file, stop=9999)
    before = mapping_file.read_bytes()

    with pytest.raises(ValueError, match="exhausted"):
        zn.redact("Alice ... Bob", ("person",), numbered_entities=True)
    assert mapping_file.read_bytes() == before
    # The attempted allocation did not consume the last available ID.
    result = zn.redact("Carol", ("person",), numbered_entities=True)
    assert result.anonymized_text == "person_9999_REDACTED"
