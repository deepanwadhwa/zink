import json
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
