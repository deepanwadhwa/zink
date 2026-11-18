"""Exercise copied examples from the README and tutorial."""

import json
from pathlib import Path
import re
from textwrap import dedent

import pytest

import zink

ROOT = Path(__file__).resolve().parents[1]


def readme_example(heading):
    path = ROOT / "README.md"
    section = path.read_text(encoding="utf-8").split(heading, 1)[1]
    snippet = section.split("```python\n", 1)[1].split("```", 1)[0]
    return compile(snippet, str(path), "exec")


def folder_example():
    path = ROOT / "docs/source/tutorial.rst"
    section = path.read_text(encoding="utf-8").split(
        "5. Process a folder of text files", 1
    )[1]
    block = re.search(
        r"(?m)^\.\. code-block:: python\n\n((?:(?: {3}[^\n]*)?\n)+)", section
    )
    assert block is not None
    return compile(dedent(block[1]), str(path), "exec")


def predict_terms(terms):
    def predict(text, labels):
        matches = []
        for term, label in terms.items():
            if label in labels:
                for match in re.finditer(re.escape(term), text):
                    matches.append(
                        {
                            "start": match.start(),
                            "end": match.end(),
                            "text": match[0],
                            "label": label,
                            "score": 0.9,
                        }
                    )
        return sorted(matches, key=lambda entity: entity["start"])

    return predict


def check_numbering_example(capsys):
    namespace = {}
    exec(readme_example("### 4. Persistent Entity Mapping"), namespace)

    [first] = namespace["result1"].replacements
    [second] = namespace["result2"].replacements
    assert first.original == second.original == "Alice"
    assert first.pseudonym == second.pseudonym
    mapping_path = Path(zink.where_mapping_file())
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert first.pseudonym == f"person_{mapping['person']['Alice']}_REDACTED"
    assert capsys.readouterr().out.splitlines() == [
        f"My name is {first.pseudonym}.",
        f"{first.pseudonym} is here again.",
        str(mapping_path),
    ]


def test_readme_persistent_mapping_example(fake_extractor, capsys):
    fake_extractor(predict_terms({"Alice": "person"}))
    check_numbering_example(capsys)


@pytest.mark.integration
def test_readme_persistent_mapping_example_with_real_model(capsys):
    check_numbering_example(capsys)


def check_shield_example(capsys):
    exec(readme_example("### 3. Shielding LLM and API Calls"), {})

    prompt, restored = capsys.readouterr().out.splitlines()
    assert re.fullmatch(
        r"Mock API received: Report for person_\d+_REDACTED from company_\d+_REDACTED\.?",
        prompt,
    )
    assert restored == "Analysis for Report for John Doe from Acme Inc. is complete."


def test_readme_shield_example(fake_extractor, capsys):
    fake_extractor(predict_terms({"John Doe": "person", "Acme Inc": "company"}))
    check_shield_example(capsys)


@pytest.mark.integration
def test_readme_shield_example_with_real_model(capsys):
    check_shield_example(capsys)


def test_folder_tutorial_preserves_inputs_and_writes_redacted_outputs(
    fake_extractor,
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.chdir(tmp_path)
    notes = tmp_path / "notes"
    notes.mkdir()
    originals = {
        "interview_02.txt": "Next: Élodie.\r\n".encode(),
        "interview_01.txt": "Élodie met at the café.\n".encode(),
        "readme.md": b"Project notes",
    }
    for name, original in originals.items():
        (notes / name).write_bytes(original)
    fake_extractor(predict_terms({"Élodie": "person"}))

    example = folder_example()
    namespace = {}
    exec(example, namespace)

    destination = tmp_path / "redacted_notes"
    assert [path.name for path in sorted(destination.iterdir())] == [
        "interview_01.txt",
        "interview_02.txt",
    ]
    for name, original in originals.items():
        assert (notes / name).read_bytes() == original
        if name.endswith(".txt"):
            assert (destination / name).read_bytes() == original.replace(
                "Élodie".encode(),
                b"person_REDACTED",
            )
    assert capsys.readouterr().out.splitlines() == [
        "interview_01.txt 1",
        "interview_02.txt 1",
    ]

    with pytest.raises(FileExistsError):
        exec(example, {})
    assert (
        destination / "interview_02.txt"
    ).read_bytes() == b"Next: person_REDACTED.\r\n"

    numbered = tmp_path / "numbered_notes"
    namespace["redact_folder"](notes, numbered, numbered_entities=True)
    stored = json.loads(Path(zink.where_mapping_file()).read_text(encoding="utf-8"))
    placeholder = f"person_{stored['person']['Élodie']}_REDACTED".encode()
    for name in ("interview_01.txt", "interview_02.txt"):
        assert (numbered / name).read_bytes() == originals[name].replace(
            "Élodie".encode(),
            placeholder,
        )
