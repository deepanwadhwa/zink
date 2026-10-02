import importlib.util
from pathlib import Path
import sys
import json

import pytest

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


def test_micro_f4_counts_duplicates_boundary_errors_and_misses():
    row = {"entity_start": 3, "entity_end": 8}
    records = [
        runner.target_metrics(row, [(3, 8, "X"), (3, 8, "X"), (10, 12, "X")]),
        runner.target_metrics(row, [(3, 7, "X")]),
        runner.target_metrics(row, []),
    ]
    result = runner.summarize(records)
    assert (result["true_positives"], result["false_positives"], result["false_negatives"]) == (1, 2, 2)
    assert result["precision"] == pytest.approx(1 / 3)
    assert result["recall"] == pytest.approx(1 / 3)
    assert result["f4"] == pytest.approx(1 / 3)
    # An additional miss penalizes F4 more than an additional false positive.
    missed = runner.summarize(records + [runner.target_metrics(row, [])])
    extra = runner.summarize([runner.target_metrics(row, [(3, 8, "X"), (10, 12, "X"), (14, 16, "X")])] + records[1:])
    assert missed["f4"] < extra["f4"]
    assert runner.summarize([])["f4"] == 0


def test_rescore_uses_saved_spans_and_preserves_timings(tmp_path):
    original = {"system": "zink", "repeats": 1, "by_topic_useful": {"names": {}}, "median_seconds": 12.34}
    path = tmp_path / "results.json"
    path.write_text(json.dumps(original))
    record = {"target_start": 3, "target_end": 8, "predictions": [[3, 8, "person"]],
              "useful": True, "mapped_presidio_type": "PERSON", "topic": "names", "exact": False}
    predictions = tmp_path / "predictions-1.jsonl"
    saved = json.dumps(record) + "\n"
    predictions.write_text(saved)
    result = runner.rescore_saved_results(tmp_path)
    assert result["useful_records"]["f4"] == 1
    assert result["median_seconds"] == 12.34
    assert predictions.read_text() == saved
    assert json.loads(path.read_text()) == result
