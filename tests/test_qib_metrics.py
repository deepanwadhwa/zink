import importlib.util
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks"))
spec = importlib.util.spec_from_file_location("qib_runner", "benchmarks/qib_presidio.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_full_coverage_is_distinct_from_exact_match():
    row = {"entity_start": 3, "entity_end": 8}
    metrics = runner.target_metrics(row, [(2, 9, "PERSON")])
    assert metrics["fully_covered"]
    assert not metrics["exact"]
    assert metrics["overlap"]


def test_partial_overlap_does_not_establish_complete_redaction():
    row = {"entity_start": 3, "entity_end": 8}
    metrics = runner.target_metrics(row, [(3, 7, "PERSON")])
    assert metrics["overlap"]
    assert not metrics["fully_covered"]


def test_union_coverage_and_empty_predictions():
    row = {"entity_start": 3, "entity_end": 8}
    assert runner.target_metrics(row, [(3, 5, "X"), (5, 8, "Y")])["fully_covered"]
    assert not runner.target_metrics(row, [])["overlap"]


def test_emphasis_normalization_updates_gold_offsets():
    text = 'Visit *Paris* tomorrow.'
    start = text.index('Paris')
    row = {"passage": text, "entity_start": start, "entity_end": start + 5,
           "ground_truth_entity": "Paris"}
    normalized = runner.normalize_emphasis(row)
    assert normalized["passage"] == "Visit Paris tomorrow."
    assert normalized["entity_start"] == 6
    assert normalized["entity_end"] == 11
    assert row["passage"] == text
