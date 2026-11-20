import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from importlib import import_module
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import zink as zn
from zink.replacer import EntityReplacer


@pytest.mark.integration
def test01():
    text = "John works as a doctor and plays football after work and drives a toyota."
    labels = ("person", "profession", "sport", "car")
    q = zn.redact(text, labels)
    assert (
        "John" not in q.anonymized_text
        and "doctor" not in q.anonymized_text
        and "football" not in q.anonymized_text
        and "toyota" not in q.anonymized_text
    )


@pytest.mark.integration
def test02():
    text = "Samantha is sitting on a french chair"
    labels = ("person", "furniture")
    q = zn.redact(text, labels)
    print(q.anonymized_text)
    assert (
        "person_REDACTED" in q.anonymized_text
        and "furniture_REDACTED" in q.anonymized_text
    )


@pytest.mark.integration
def test03():
    text = "Patient, 33 years old, was admitted with a chest pain"
    labels = ("age", "medical condition")
    q = zn.replace(text, labels)
    assert (
        "33 years old" not in q.anonymized_text
        and "chest pain" not in q.anonymized_text
    )


@pytest.mark.integration
def test04():
    text = "John Doe dialled his mother at 992-234-3456 and then went out for a walk."
    labels = ("person", "phone number", "relationship")
    q = zn.redact(text, labels)
    assert (
        "John Doe" not in q.anonymized_text
        and "992-234-3456" not in q.anonymized_text
        and "mother" not in q.anonymized_text
    )


@pytest.mark.integration
def test05():
    text = "Melissa is a software engineer at Google and she drives a Tesla. She is 29 years old."
    labels = ("person", "profession", "company", "car", "age")
    my_data = {
        "person": "Alice",
        "profession": "Data Scientist",
        "company": "Amazon",
        "car": "Honda",
        "age": "35",
    }

    q = zn.replace_with_my_data(text, labels, user_replacements=my_data)

    # Check original sensitive data is not present
    for original in ["Melissa", "software engineer", "Google", "Tesla", "29 years old"]:
        assert original not in q.anonymized_text, f"'{original}' was not replaced!"

    # Optionally check that replacements are correctly inserted
    for replacement in my_data.values():
        if isinstance(replacement, (list, tuple)):
            assert any(rep in q.anonymized_text for rep in replacement), (
                "Replacement not found in anonymized text."
            )
        else:
            assert replacement in q.anonymized_text, (
                f"Replacement '{replacement}' missing."
            )

    print("test05 passed successfully.")


@pytest.mark.integration
def test06():
    # Test a purely numeric date – no explicit month name,
    # so DateReplacementStrategy should simply return a faker.date()
    text = "The meeting is scheduled on 10/22/2020 at the main office."
    labels = ("date",)
    q = zn.replace(text, labels)
    # Ensure that the original numeric date is removed and replaced by a new date format (e.g., with hyphens)
    assert "10/22/2020" not in q.anonymized_text and "-" in q.anonymized_text, (
        "Numeric date not replaced properly"
    )


@pytest.mark.integration
def test07():
    # Test a sentence with two human names in a medical context.
    # The human_entity_roles logic should replace both names.
    text = "Dr. John Doe operated on patient Peter Baxter."
    labels = ("person",)
    q = zn.redact(text, labels)
    # Check that both names have been replaced (i.e. original names do not appear)
    assert (
        "John Doe" not in q.anonymized_text and "Peter Baxter" not in q.anonymized_text
    ), "One or both human names were not replaced"


@pytest.mark.integration
def test08():
    # Test a location where the text is a country (using countries_data via file).
    text = "The conference was held in Japan."
    labels = ("location",)
    q = zn.redact(text, labels)
    # Ensure "Japan" is not present; it should be replaced by another country
    assert "japan" not in q.anonymized_text.lower(), (
        "Country name 'Japan' was not replaced"
    )


@pytest.mark.integration
def test09():
    # Test combined labels: person and location.
    text = "Alice, the engineer, from United States of America, called her friend."
    labels = ("person", "location")
    q = zn.redact(text, labels)
    # Check that "Alice" is replaced and that the country (or its synonyms) is replaced
    assert (
        "alice" not in q.anonymized_text.lower()
        and "united states" not in q.anonymized_text.lower()
    ), "Either the person or location was not replaced properly"


@pytest.mark.integration
def test10():
    # Test a multi-label scenario including a date, to exercise delegation to DateReplacementStrategy.
    text = "Dr. Michael, a cardiologist from Canada, was born on 07/04/1970."
    labels = ("person", "profession", "location", "date")
    q = zn.redact(text, labels)
    # Check that sensitive elements are removed from the anonymized text.
    for original in ["Dr. Michael", "cardiologist", "Canada", "07/04/1970"]:
        assert original.lower() not in q.anonymized_text.lower(), (
            f"'{original}' was not replaced!"
        )


@pytest.mark.integration
def test11():
    text = "John, who is from Japan moved to the USA last month. u"
    labels = ("name", "location")
    q = zn.redact(text, labels)
    # Check that the original name and locations do not appear.
    assert "john" not in q.anonymized_text.lower(), "Original name 'John' found"
    assert "japan" not in q.anonymized_text.lower(), "Original location 'Japan' found"
    assert "usa" not in q.anonymized_text.lower(), "Original location 'USA' found"
    print("test12 passed:", q.anonymized_text)


@pytest.mark.integration
def test12():
    text = "John riggins, who is from Japan moved to the USA last month. u"
    labels = ("name", "location")
    q = zn.redact(text, labels)
    # Ensure that both first and last names are replaced.
    assert "John riggins" not in q.anonymized_text.lower(), "Original name 'John' found"
    # Ensure that the locations are replaced.
    assert "japan" not in q.anonymized_text.lower(), "Original location 'Japan' found"
    assert "usa" not in q.anonymized_text.lower(), "Original location 'USA' found"
    print("test13 passed:", q.anonymized_text)


@pytest.mark.integration
def test13():
    t0 = "Amy Poehler is a great comedian just like Tina Fey, but Amy is from Minnesota unlike Tina."
    labels = ("person",)
    q = zn.redact(t0, labels)
    assert "Amy Poehler" not in q.anonymized_text
    assert "Tina Fey" not in q.anonymized_text
    assert "Amy" not in q.anonymized_text
    assert "Tina" not in q.anonymized_text
    print("test14 passed:", q.anonymized_text)


def _entity(text, start, end, label="person"):
    return {
        "start": start,
        "end": end,
        "label": label,
        "text": text[start:end],
        "score": 0.95,
    }


@pytest.fixture
def detections(fake_extractor):
    """Supply exact entities while exercising the public transformation path."""
    spans = {}
    calls = []

    def extract(text, categories):
        calls.append((text, tuple(categories or ())))
        return [entity.copy() for entity in spans[text]]

    fake_extractor(extract)
    return spans, calls


@pytest.mark.parametrize("entrypoint", [zn.replace, zn.replace_with_my_data])
@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_replace_ann_and_annette_by_span(detections, entrypoint, ensure_consistency):
    text = "Ann met Annette; Ann arrived later."
    spans, _ = detections
    spans[text] = [_entity(text, *bounds) for bounds in [(0, 3), (8, 15), (17, 20)]]

    result = entrypoint(
        text,
        categories=("person",),
        user_replacements={"PERSON": "Alice"},
        ensure_consistency=ensure_consistency,
    )

    assert result.original_text == text
    assert result.anonymized_text == "Alice met Alice; Alice arrived later."
    assert result.replacements == [
        {**entity, "source": "user"} for entity in spans[text]
    ]
    assert result.features["num_replacements"] == 3


@pytest.mark.parametrize(
    ("text", "spans", "expected"),
    [
        ("Ann met Annette.", [(0, 3)], "Alice met Annette."),
        ("Ann met Ann.", [(8, 11)], "Ann met Alice."),
        ("Annette met Ann.", [(12, 15)], "Annette met Alice."),
        ("", [], ""),
        ("Nobody was detected.", [], "Nobody was detected."),
    ],
)
@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_replace_leaves_undetected_text_intact(
    detections, text, spans, expected, ensure_consistency
):
    detected, _ = detections
    detected[text] = [_entity(text, *bounds) for bounds in spans]

    result = zn.replace(
        text,
        categories=("person",),
        user_replacements={"person": "Alice"},
        ensure_consistency=ensure_consistency,
        use_cache=False,
    )

    assert result.anonymized_text == expected
    assert result.features["num_replacements"] == len(spans)


@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_replace_does_not_rewrite_inserted_text(detections, ensure_consistency):
    text = "Ana met João at Żółć."
    spans, _ = detections
    spans[text] = [
        _entity(text, 0, 3),
        _entity(text, 8, 12, "contact"),
        _entity(text, 16, 20, "location"),
    ]

    result = zn.replace_with_my_data(
        text,
        categories=("person", "contact", "location"),
        user_replacements={"person": "João II", "contact": "Léa", "location": ""},
        ensure_consistency=ensure_consistency,
    )

    assert result.anonymized_text == "João II met Léa at ."
    assert [(entity["start"], entity["end"]) for entity in result.replacements] == [
        (0, 3),
        (8, 12),
        (16, 20),
    ]


@pytest.mark.parametrize(
    ("ensure_consistency", "expected_text", "expected_selections"),
    [
        (True, "Céline\n...\nCéline", 1),
        (False, "Céline\n...\nBob", 2),
    ],
)
def test_replace_candidates_per_call(
    monkeypatch, detections, ensure_consistency, expected_text, expected_selections
):
    text = "Zoë\n...\nZoë"
    spans, _ = detections
    spans[text] = [_entity(text, 0, 3), _entity(text, 8, 11)]
    selections = []

    def choose(candidates):
        candidate = candidates[len(selections)]
        selections.append(candidate)
        return candidate

    replacement_module = import_module("zink.replacer.replacer")
    monkeypatch.setattr(replacement_module.random, "choice", choose)

    result = zn.replace(
        text,
        categories=("person",),
        user_replacements={"person": ["Céline", "Bob"]},
        ensure_consistency=ensure_consistency,
    )

    assert result.anonymized_text == expected_text
    assert len(selections) == expected_selections
    assert [entity["source"] for entity in result.replacements] == ["user", "user"]


@pytest.mark.parametrize("ensure_consistency", [True, False])
@pytest.mark.parametrize("unusable", [None, "Ann"])
def test_replacer_redacts_when_replacement_would_leave_source(
    ensure_consistency, unusable
):
    text = "Ann met Ann."
    entities = [_entity(text, 0, 3), _entity(text, 8, 11)]
    replacer = EntityReplacer()
    replace = (
        replacer.replace_entities_ensure_consistency
        if ensure_consistency
        else replacer.replace_entities
    )

    assert replace(entities, text, {"person": unusable}) == (
        "person_REDACTED met person_REDACTED."
    )
    assert [entity["source"] for entity in entities] == ["redaction", "redaction"]


@pytest.mark.parametrize("ensure_consistency", [True, False])
@pytest.mark.parametrize("use_json_mapping", [True, False])
def test_replacer_uses_faker_or_fallback_for_unmapped_labels(
    monkeypatch, ensure_consistency, use_json_mapping
):
    text = "555-0100 near Oak."
    entities = [_entity(text, 0, 8, "phone_number"), _entity(text, 14, 17, "trail")]
    strategy_module = import_module("zink.replacer.rfakerjson")
    mapping_module = import_module("zink.replacer.json_mapping")

    class FakeFaker:
        def phone_number(self):
            return "555-0200"

    monkeypatch.setattr(strategy_module, "Faker", FakeFaker)
    replacer = EntityReplacer(use_json_mapping=use_json_mapping)
    replace = (
        replacer.replace_entities_ensure_consistency
        if ensure_consistency
        else replacer.replace_entities
    )

    fallback = "Pine" if use_json_mapping else "[REDACTED]"
    with monkeypatch.context() as fake_data:
        fake_data.setattr(mapping_module, "load_mapping", lambda: {"trail": ["Pine"]})
        assert replace(entities, text, {"person": "Alice"}) == (
            f"555-0200 near {fallback}."
        )
    assert [entity["source"] for entity in entities] == [
        "faker",
        "json" if use_json_mapping else "default",
    ]


@pytest.mark.parametrize("use_cache", [True, False])
def test_replace_preserves_prior_results_when_reusing_detections(detections, use_cache):
    text = "Ann waited."
    spans, calls = detections
    spans[text] = [_entity(text, 0, 3)]

    first = zn.replace(
        text, ("person",), user_replacements={"person": "Alice"}, use_cache=use_cache
    )
    second = zn.replace(
        text, ("person",), user_replacements={"person": "Ann"}, use_cache=use_cache
    )
    assert first.anonymized_text == "Alice waited."
    assert second.anonymized_text == "person_REDACTED waited."
    assert first.replacements == [{**spans[text][0], "source": "user"}]
    assert second.replacements == [{**spans[text][0], "source": "redaction"}]
    assert len(calls) == (1 if use_cache else 2)


@pytest.mark.parametrize("ensure_consistency", [True, False])
def test_concurrent_replacements_use_separate_mappings(
    detections, monkeypatch, ensure_consistency
):
    first_text = "Ann met Bob."
    second_text = "Eve waited."
    spans, _ = detections
    spans[first_text] = [_entity(first_text, 0, 3), _entity(first_text, 8, 11)]
    spans[second_text] = [_entity(second_text, 0, 3)]
    choosing = Event()
    resume = Event()

    def choose(candidates):
        choosing.set()
        assert resume.wait(timeout=5), "First request was not resumed"
        return candidates[0]

    replacement_module = import_module("zink.replacer.replacer")
    monkeypatch.setattr(replacement_module.random, "choice", choose)

    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(
            zn.replace,
            first_text,
            ("person",),
            {"person": ["Alice"]},
            ensure_consistency=ensure_consistency,
            use_cache=False,
        )
        try:
            assert choosing.wait(timeout=5), "First request did not reach selection"
            second = zn.replace(
                second_text, ("person",), {"person": "David"}, use_cache=False
            )
        finally:
            resume.set()
        first_result = first.result(timeout=5)

    assert second.anonymized_text == "David waited."
    assert first_result.anonymized_text == "Alice met Alice."


@pytest.mark.integration
def test_replace_only_detected_spans_with_real_model():
    text = "Ann met Annette; Ann arrived later."
    result = zn.replace(text, ("person",), user_replacements={"person": "Alice"})

    assert [entity["text"] for entity in result.replacements] == [
        "Ann",
        "Annette",
        "Ann",
    ]
    assert result.anonymized_text == "Alice met Alice; Alice arrived later."


def _readme_custom_replacement_example():
    readme = Path(__file__).resolve().parents[2] / "README.md"
    section = readme.read_text(encoding="utf-8").split(
        "### 2. Custom Replacements (Bring Your Own Data)", 1
    )[1]
    return section.split("```python\n", 1)[1].split("```", 1)[0]


def test_readme_custom_replacement_example(detections, monkeypatch, capsys):
    text = "Melissa works at Google and drives a Tesla."
    spans, _ = detections
    spans[text] = [
        _entity(text, 0, 7),
        _entity(text, 17, 23, "company"),
        _entity(text, 37, 42, "car"),
    ]
    replacement_module = import_module("zink.replacer.replacer")
    monkeypatch.setattr(
        replacement_module.random, "choice", lambda candidates: candidates[0]
    )

    exec(_readme_custom_replacement_example(), {})

    assert capsys.readouterr().out == "Alice works at OpenAI and drives a Honda.\n"


@pytest.mark.integration
def test_readme_custom_replacement_example_with_real_model(capsys):
    exec(_readme_custom_replacement_example(), {})

    assert capsys.readouterr().out.strip() in {
        "Alice works at OpenAI and drives a Honda.",
        "Alice works at OpenAI and drives a Toyota.",
    }


@pytest.mark.parametrize(
    "options", [{}, {"user_replacements": {}}, {"user_replacements": None}]
)
def test_replace_with_my_data_requires_nonempty_mapping(options):
    with pytest.raises(ValueError, match="non-empty"):
        zn.replace_with_my_data("Ann waited.", categories=("person",), **options)


def test_redact_custom_placeholder_reports_original_span(detections):
    text = "Ann waited."
    spans, _ = detections
    spans[text] = [_entity(text, 0, 3)]

    result = zn.redact(
        text, categories=("person",), placeholder="[NAME]", use_cache=False
    )

    assert result.anonymized_text == "[NAME] waited."
    assert result.features["num_replacements"] == 1
    (replacement,) = result.replacements
    assert (replacement.start, replacement.end) == (0, 3)
    assert replacement.original == "Ann"
    assert replacement.pseudonym == "[NAME]"


@pytest.mark.parametrize(
    ("original", "label", "faker_results", "expected"),
    [
        (
            "10/22/2020",
            "date",
            {"random_int": [(date(2001, 5, 24) - date(1900, 1, 1)).days]},
            "2001-05-24",
        ),
        (
            "Jul 13 2000",
            "date",
            {
                "month_name": ["July", "February"],
                "random_int": [13, 12],
                "year": ["2000", "2003"],
            },
            "February 12 2003",
        ),
        (
            "September 30 2001",
            "date",
            {"month_name": ["March"], "random_int": [17], "year": ["2020"]},
            "March 17 2020",
        ),
        (
            "January 2020",
            "date",
            {"month_name": ["January", "June"], "year": ["2020", "2004"]},
            "June 2004",
        ),
        (
            "Tuesday Jan 2006",
            "date",
            {
                "month_name": ["February"],
                "day_of_week": ["Tuesday", "Monday"],
                "year": ["2024"],
            },
            "February Monday 2024",
        ),
        ("May", "month name", {"month_name": ["June"]}, "June"),
        (
            "Monday",
            "weekday",
            {"day_of_week": ["Monday", "Friday"]},
            "Friday",
        ),
        (
            "Jan 03 2000",
            "date",
            {"month_name": ["July"], "random_int": [3, 12], "year": ["2003"]},
            "July 12 2003",
        ),
    ],
)
def test_replace_dates_with_matching_components(
    detections, monkeypatch, original, label, faker_results, expected
):
    date_module = import_module("zink.replacer.rdate")
    methods = {name: Mock(side_effect=values) for name, values in faker_results.items()}
    monkeypatch.setattr(date_module, "Faker", lambda: SimpleNamespace(**methods))

    text = f"Scheduled for {original}; keep this note."
    start = text.index(original)
    spans, _ = detections
    spans[text] = [_entity(text, start, start + len(original), label)]

    result = zn.replace(text, categories=[label])

    assert result.anonymized_text == f"Scheduled for {expected}; keep this note."
    assert result.replacements == [{**spans[text][0], "source": "rdate"}]


@pytest.mark.parametrize(
    ("pick_upper", "expected"), [(False, "2001-06-01"), (True, "2001-06-04")]
)
def test_date_fallback_honors_both_ends_of_its_date_range(
    monkeypatch, pick_upper, expected
):
    date_module = import_module("zink.replacer.rdate")
    start_date, end_date = datetime(2001, 6, 1), datetime(2001, 6, 4)

    def pick_offset(*, min, max):
        assert (min, max) == (0, 3)
        return max if pick_upper else min

    monkeypatch.setattr(
        date_module,
        "Faker",
        lambda: SimpleNamespace(month_name=lambda: "January", random_int=pick_offset),
    )
    strategy = date_module.DateReplacementStrategy(
        start_date=start_date, end_date=end_date
    )

    assert strategy.replace({"text": "January"}) == expected


@pytest.mark.parametrize("range_end", [1, 4])
def test_numeric_date_honors_range_and_never_reuses_source_date(monkeypatch, range_end):
    date_module = import_module("zink.replacer.rdate")
    start_date, end_date = datetime(2001, 6, 1), datetime(2001, 6, range_end)

    def choose_source_offset(*, min, max):
        assert (min, max) == (0, range_end - 1)
        return min

    monkeypatch.setattr(
        date_module,
        "Faker",
        lambda: SimpleNamespace(random_int=choose_source_offset),
    )
    strategy = date_module.DateReplacementStrategy(
        start_date=start_date, end_date=end_date
    )

    result = strategy.replace({"text": "06/01/2001"})

    if range_end == 1:
        assert result is None
    else:
        assert date(2001, 6, 1) < date.fromisoformat(result) <= date(2001, 6, range_end)


@pytest.mark.parametrize("pick_end", [False, True])
def test_numeric_date_excludes_both_readings_of_ambiguous_slash_date(
    monkeypatch, pick_end
):
    date_module = import_module("zink.replacer.rdate")
    start, end = date(2001, 1, 6), date(2001, 6, 1)
    monkeypatch.setattr(
        date_module,
        "Faker",
        lambda: SimpleNamespace(
            random_int=lambda *, min, max: max if pick_end else min
        ),
    )

    value = date_module.DateReplacementStrategy(start, end).replace(
        {"text": "06/01/2001"}
    )

    assert start < date.fromisoformat(value) < end


def test_date_replacement_rejects_reversed_date_range():
    date_module = import_module("zink.replacer.rdate")
    with pytest.raises(ValueError, match="start_date must be on or before end_date"):
        date_module.DateReplacementStrategy(datetime(2025, 1, 2), date(2025, 1, 1))


@pytest.mark.skipif(
    not hasattr(time, "tzset"), reason="subprocess requires POSIX timezone support"
)
def test_single_day_iso_replacement_keeps_calendar_date_in_tokyo():
    script = """
from datetime import datetime
from zink.replacer.rdate import DateReplacementStrategy

only_date = datetime(1900, 1, 1)
assert only_date.astimezone().utcoffset().total_seconds() > 0
assert DateReplacementStrategy(only_date, only_date).replace({'text': 'unknown'}) == '1900-01-01'
"""
    subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        env={**os.environ, "TZ": "Asia/Tokyo"},
        timeout=30,
    )


@pytest.mark.parametrize(
    ("original", "label", "recognized", "fake_method", "candidates", "expected"),
    [
        (
            "Alice Brown",
            "nurse name",
            True,
            "name",
            ["Alice Hill", "Kelly Brown", "Dora White"],
            "Dora White",
        ),
        ("Ann", "doctor", True, "first_name", ["ann", "Edna"], "Edna"),
        ("Ann", "doctor", True, "first_name", ["Ann Marie", "Edna"], "Edna"),
        ("Pat", "doctor", True, "first_name", ["PAT"] * 10, "[doctor_REDACTED]"),
        (
            "Alice Brown",
            "doctor",
            True,
            "name",
            ["Alice Gray"] * 10,
            "[doctor_REDACTED]",
        ),
        ("cardiology", "doctor_name", False, None, [], "[doctor_name_REDACTED]"),
    ],
)
def test_replace_person_roles_avoids_source_name_tokens(
    detections,
    monkeypatch,
    original,
    label,
    recognized,
    fake_method,
    candidates,
    expected,
):
    person_module = import_module("zink.replacer.rperson")
    outputs = iter(candidates)
    faker_methods = {fake_method: lambda: next(outputs)} if fake_method else {}
    monkeypatch.setattr(
        person_module, "Faker", lambda: SimpleNamespace(**faker_methods)
    )

    def classify(text, labels):
        assert (text, labels) == (original, ("name",))
        return [_entity(text, 0, len(text), "name")] if recognized else []

    monkeypatch.setattr(
        person_module, "_DEFAULT_EXTRACTOR", SimpleNamespace(predict=classify)
    )
    text = f"Assigned to {original}, pending review."
    start = text.index(original)
    spans, _ = detections
    spans[text] = [_entity(text, start, start + len(original), label)]

    result = zn.replace(text, categories=[label])

    assert result.anonymized_text == f"Assigned to {expected}, pending review."
    assert result.replacements == [{**spans[text][0], "source": "rperson"}]


@pytest.mark.parametrize("use_json_mapping", [True, False])
@pytest.mark.parametrize("faker_raises", [True, False])
def test_replace_falls_back_if_faker_fails_or_returns_original(
    monkeypatch, use_json_mapping, faker_raises
):
    strategy_module = import_module("zink.replacer.rfakerjson")
    mapping_module = import_module("zink.replacer.json_mapping")
    original = "555-0100"

    class FakeFaker:
        def phone_number(self):
            if faker_raises:
                raise RuntimeError("provider could not generate a phone number")
            return original

    monkeypatch.setattr(strategy_module, "Faker", FakeFaker)
    with monkeypatch.context() as fake_data:
        fake_data.setattr(
            mapping_module, "load_mapping", lambda: {"phone_number": ["555-0200"]}
        )
        entity = _entity(original, 0, len(original), "phone_number")
        result = EntityReplacer(use_json_mapping=use_json_mapping).replace_entities(
            [entity], original
        )

    assert result == ("555-0200" if use_json_mapping else "[REDACTED]")
    assert entity["source"] == ("json" if use_json_mapping else "default")


def test_replace_country_and_city_use_different_location_providers(
    detections, monkeypatch
):
    strategy_module = import_module("zink.replacer.rfakerjson")
    monkeypatch.setattr(
        strategy_module, "Faker", lambda: SimpleNamespace(city=lambda: "Oakdale")
    )
    monkeypatch.setattr(
        strategy_module.random,
        "choice",
        lambda choices: next(country for country in choices if country == "france"),
    )
    text = "Japan and Oldtown."
    spans, _ = detections
    spans[text] = [_entity(text, 0, 5, "location"), _entity(text, 10, 17, "location")]

    result = zn.replace(text, categories=["location"])

    assert result.anonymized_text == "France and Oakdale."
    assert [entity["source"] for entity in result.replacements] == [
        "faker_country",
        "faker",
    ]


@pytest.mark.parametrize("entrypoint", [zn.replace, zn.replace_with_my_data])
@pytest.mark.parametrize("reverse_labels", [False, True])
@pytest.mark.parametrize("ensure_consistency", [None, True, False])
@pytest.mark.parametrize("scope", [None, "text", "label"])
def test_replacement_consistency_preserves_default_and_supports_label_opt_in(
    detections, entrypoint, reverse_labels, ensure_consistency, scope
):
    text = "Jordan met Jordan; Jordan returned."
    first, second = ("location", "person") if reverse_labels else ("person", "location")
    values = {"person": "Alice", "location": "Venice"}
    spans, _ = detections
    spans[text] = [
        _entity(text, 0, 6, first),
        _entity(text, 11, 17, second),
        _entity(text, 19, 25, first.upper()),
    ]
    kwargs = {"user_replacements": values}
    if ensure_consistency is not None:
        kwargs["ensure_consistency"] = ensure_consistency
    if scope is not None:
        kwargs["consistency_scope"] = scope
    result = entrypoint(text, **kwargs)
    text_wide = ensure_consistency is not False and scope != "label"
    middle = first if text_wide else second
    assert result.anonymized_text == (
        f"{values[first]} met {values[middle]}; {values[first]} returned."
    )
    assert [entity["source"] for entity in result.replacements] == ["user"] * 3


@pytest.mark.parametrize("entrypoint", [zn.replace, zn.replace_with_my_data])
@pytest.mark.parametrize("ensure_consistency", [True, False])
@pytest.mark.parametrize("lowercase_last", [False, True])
@pytest.mark.parametrize("scope", [None, "text", "label"])
def test_consistency_scopes_reuse_list_choices_and_respect_exact_source_case(
    detections, monkeypatch, entrypoint, ensure_consistency, lowercase_last, scope
):
    last = "jordan" if lowercase_last else "Jordan"
    text = f"Jordan met Jordan; {last} returned."
    spans, _ = detections
    spans[text] = [
        _entity(text, 0, 6, "person"),
        _entity(text, 11, 17, "location"),
        _entity(text, 19, 25, "PERSON"),
    ]
    seen = {"Alice": 0, "Venice": 0}

    def choose(values):
        key = values[0]
        index = seen[key]
        seen[key] += 1
        return values[index]

    monkeypatch.setattr("zink.replacer.replacer.random.choice", choose)
    kwargs = {} if scope is None else {"consistency_scope": scope}
    result = entrypoint(
        text,
        user_replacements={"PERSON": ["Alice", "Bea"], "location": ["Venice"]},
        ensure_consistency=ensure_consistency,
        **kwargs,
    )
    reused = ensure_consistency and not lowercase_last
    expected_last = "Alice" if reused else "Bea"
    text_wide = ensure_consistency and scope != "label"
    middle = "Alice" if text_wide else "Venice"
    assert result.anonymized_text == f"Alice met {middle}; {expected_last} returned."
    assert seen == {"Alice": 1 if reused else 2, "Venice": 0 if text_wide else 1}


@pytest.mark.parametrize("entrypoint", [zn.replace, zn.replace_with_my_data])
@pytest.mark.parametrize("ensure_consistency", [True, False])
@pytest.mark.parametrize("scope", [None, "", "Label", "entity", [], 42])
def test_invalid_consistency_scope_fails_before_extraction(
    entrypoint, ensure_consistency, scope
):
    def unexpected_prediction(*args, **kwargs):
        pytest.fail("Invalid scope must fail before calling the extractor")

    with pytest.raises(ValueError, match="consistency_scope must be 'text' or 'label'"):
        entrypoint(
            "Jordan met Jordan.",
            user_replacements={"person": "Alice", "location": "Venice"},
            ensure_consistency=ensure_consistency,
            consistency_scope=scope,
            extractor=SimpleNamespace(predict2=unexpected_prediction),
        )


@pytest.mark.parametrize("entrypoint", [zn.replace, zn.replace_with_my_data])
def test_alternating_scopes_does_not_leak_choices_between_calls(detections, entrypoint):
    text = "Jordan met Jordan."
    spans, calls = detections
    spans[text] = [_entity(text, 0, 6, "person"), _entity(text, 11, 17, "location")]
    values = {"person": "Alice", "location": "Venice"}
    outputs = [
        entrypoint(
            text, user_replacements=values, consistency_scope=scope
        ).anonymized_text
        for scope in ("text", "label", "text")
    ]
    assert outputs == ["Alice met Alice.", "Alice met Venice.", "Alice met Alice."]
    assert len(calls) == (1 if entrypoint is zn.replace else 3)


def test_concurrent_requests_choose_their_own_consistency_scope(detections):
    text = "Jordan met Jordan."
    spans, _ = detections
    spans[text] = [_entity(text, 0, 6, "person"), _entity(text, 11, 17, "location")]
    scopes = ["text", "label"] * 5

    def replace(scope):
        return zn.replace(
            text,
            user_replacements={"person": "Alice", "location": "Venice"},
            consistency_scope=scope,
        ).anonymized_text

    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(replace, scopes))
    assert outputs == ["Alice met Alice.", "Alice met Venice."] * 5


@pytest.mark.parametrize("scope", [None, "text", "label"])
def test_direct_replacer_keeps_text_default_and_supports_label_scope(scope):
    text = "Jordan met Jordan."
    entities = [_entity(text, 0, 6, "person"), _entity(text, 11, 17, "location")]
    kwargs = {} if scope is None else {"consistency_scope": scope}
    result = EntityReplacer().replace_entities_ensure_consistency(
        entities, text, {"person": "Alice", "location": "Venice"}, **kwargs
    )
    assert result == ("Alice met Venice." if scope == "label" else "Alice met Alice.")


def test_direct_replacer_rejects_invalid_consistency_scope():
    with pytest.raises(ValueError, match="consistency_scope"):
        EntityReplacer().replace_entities_ensure_consistency(
            [], "", consistency_scope="unknown"
        )
