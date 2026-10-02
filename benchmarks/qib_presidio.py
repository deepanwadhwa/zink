"""Pinned QIB target-detection evaluation. See QIB-COMPARISON.md."""
import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import statistics
import time
import urllib.request

from compare_presidio import peak_rss_mib

REVISION = "af345705a03852b8bd77c2e69c971a0361b1e71d"
FILENAME = "qib_validated_with_indices_filtered_useful.json"
URL = f"https://huggingface.co/datasets/deepanwa/QIB/resolve/{REVISION}/{FILENAME}"
# Conservative semantic mappings, fixed before inspecting model predictions.
PERSON = set("PERSON PERSON_NAME LAST_NAME FAMILY_NAME GIVEN_NAME AUTHOR ARTIST MUSICIAN MUSIC_ARTIST ACTOR HISTORICAL_FIGURE PLAYER_NAME COMPOSER PAINTER CELEBRITY ARCHITECT MUSICAL_ARTIST ATHLETE CHEF SCIENTIST ASTRONAUT".split())
LOCATION = set("CITY TOWN COUNTRY LOCATION LOCATION_NAME GEOGRAPHICAL_PLACE REGION ISLAND ISLAND_GROUP NEIGHBORHOOD RIVER_NAME LAKE_NAME LAKE BEACH BEACH_NAME MOUNTAIN_RANGE DESERT BODY_OF_WATER LANDFORM".split())
MAPPING = {**{label: "PERSON" for label in PERSON}, **{label: "LOCATION" for label in LOCATION}}


def target_metrics(row, predictions):
    start, end = row["entity_start"], row["entity_end"]
    spans = {(p[0], p[1]) for p in predictions}
    exact = (start, end) in spans
    # Union coverage detects whether redaction would remove every target character.
    covered = all(any(a <= position < b for a, b in spans) for position in range(start, end))
    overlap = any(a < end and b > start for a, b in spans)
    return {"exact": exact, "fully_covered": covered, "overlap": overlap,
            "predicted_spans": len(spans), "nonmatching_spans": sum((a, b) != (start, end) for a, b in spans)}


def summarize(records):
    n = len(records)
    result = {"documents": n}
    for metric in ["exact", "fully_covered", "overlap"]:
        count = sum(r[metric] for r in records)
        result[metric + "_count"] = count
        result[metric + "_rate"] = count / n if n else None
    result["predicted_spans"] = sum(r["predicted_spans"] for r in records)
    result["nonmatching_spans"] = sum(r["nonmatching_spans"] for r in records)
    tp = result["exact_count"]
    fp = result["nonmatching_spans"]
    fn = n - tp
    result.update({
        "true_positives": tp, "false_positives": fp, "false_negatives": fn,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "recall": tp / (tp + fn) if tp + fn else 0.0,
        "f4": 17 * tp / (17 * tp + 16 * fn + fp) if tp + fn + fp else 0.0,
    })
    return result


def rescore_saved_results(directory):
    """Recompute quality metrics from the last recorded pass; preserve timings."""
    path = directory / "results.json"
    result = json.loads(path.read_text())
    predictions = directory / f"predictions-{result['repeats']}.jsonl"
    records = [json.loads(line) for line in predictions.read_text().splitlines()]
    for record in records:
        row = {"entity_start": record["target_start"], "entity_end": record["target_end"]}
        record.update(target_metrics(row, record["predictions"]))
        shared_predictions = ([p for p in record["predictions"] if p[2] == record["mapped_presidio_type"]]
                              if result["system"] == "presidio" else record["predictions"])
        record["shared_metrics"] = target_metrics(row, shared_predictions)
    useful = [r for r in records if r["useful"]]
    result.update({
        "all_records": summarize(records),
        "useful_records": summarize(useful),
        "shared_useful_records": summarize([r["shared_metrics"] for r in useful if r["mapped_presidio_type"]]),
        "outside_shared_useful_records": summarize([r for r in useful if not r["mapped_presidio_type"]]),
        "by_topic_useful": {topic: summarize([r for r in useful if r["topic"] == topic])
                            for topic in result["by_topic_useful"]},
    })
    path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def normalize_emphasis(row):
    """Remove QIB asterisk formatting, adjusting offsets identically for both tools."""
    text = row["passage"]
    start, end = row["entity_start"], row["entity_end"]
    row = dict(row)
    row["passage"] = text.replace("*", "")
    row["entity_start"] = start - text[:start].count("*")
    row["entity_end"] = end - text[:end].count("*")
    row["ground_truth_entity"] = row["ground_truth_entity"].replace("*", "")
    assert row["passage"][row["entity_start"]:row["entity_end"]] == row["ground_truth_entity"]
    return row


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--system", choices=["zink", "presidio", "presidio-gliner"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--rescore", type=Path, help="Update saved quality metrics without downloads or model inference")
    parser.add_argument("--corpus", type=Path, help="Downloaded corpus path (default: OUTPUT/corpus.json)")
    parser.add_argument("--anonymize", action="store_true", help="Include Presidio placeholder replacement in inference timing")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.rescore:
        if args.system or args.output:
            parser.error("Use --rescore on its own, without --system or --output")
        print(json.dumps(rescore_saved_results(args.rescore)["useful_records"], indent=2))
        return
    if not args.system or not args.output:
        parser.error("--system and --output are required for a new run")
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    if args.output.exists():
        parser.error("Output already exists; choose a new output directory")
    args.output.mkdir(parents=True)
    # Always fetch pinned bytes, validating any local cache against the pinned source.
    with urllib.request.urlopen(URL, timeout=60) as response:
        raw = response.read()
    (args.corpus or args.output / "corpus.json").write_bytes(raw)
    grouped = json.loads(raw)
    rows = [dict(row, topic=topic) for topic, group in grouped.items() for row in group]
    for row in rows:
        if row["passage"][row["entity_start"]:row["entity_end"]] != row["ground_truth_entity"]:
            raise ValueError(f"Invalid source annotation: {row['uuid']}")
    normalized_count = sum("*" in row["passage"] for row in rows)
    rows = [normalize_emphasis(row) for row in rows]
    if args.limit:
        rows = rows[:args.limit]
    baseline = peak_rss_mib()
    start = time.perf_counter()
    if args.system == "zink":
        import zink
        def run(row):
            # Annotation-assisted semantic prompt: target value and offsets are never supplied.
            label = row["ground_truth_label"].lower().replace("_", " ")
            result = zink.redact(row["passage"], categories=(label,), use_cache=False, auto_parallel=False)
            return [(p.start, p.end, p.label) for p in result.replacements]
        packages = ["zink", "gliner", "onnxruntime", "torch", "transformers"]
    else:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        engine = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm" if args.system == "presidio-gliner" else "en_core_web_lg"}],
        }).create_engine()
        analyzer = AnalyzerEngine(nlp_engine=engine, supported_languages=["en"])
        if args.system == "presidio-gliner":
            from presidio_analyzer.predefined_recognizers import GLiNERRecognizer
            entity_mapping = {row["ground_truth_label"].lower().replace("_", " "): row["ground_truth_label"] for row in rows}
            gliner_recognizer = GLiNERRecognizer(
                model_name="urchade/gliner_multi_pii-v1",
                revision="1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d",
                entity_mapping=entity_mapping,
                flat_ner=False, multi_label=True, map_location="cpu",
            )
            analyzer.registry.add_recognizer(gliner_recognizer)
            analyzer.registry.remove_recognizer("SpacyRecognizer")
        supported = analyzer.get_supported_entities("en")
        if args.anonymize:
            from presidio_anonymizer import AnonymizerEngine
            anonymizer = AnonymizerEngine()
        def run(row):
            if args.system == "presidio-gliner":
                # Only the current semantic prompt is used; registration supports all QIB labels.
                gliner_recognizer.gliner_labels = [row["ground_truth_label"].lower().replace("_", " ")]
                entities = [row["ground_truth_label"]]
            else:
                entities = supported
            spans = analyzer.analyze(
                text=row["passage"], language="en", entities=entities, score_threshold=0.0)
            predictions = [(p.start, p.end, p.entity_type) for p in spans]
            if args.anonymize:
                anonymizer.anonymize(text=row["passage"], analyzer_results=spans)
            return predictions
        packages = ["presidio-analyzer", "spacy", "en-core-web-sm" if args.system == "presidio-gliner" else "en-core-web-lg"]
        if args.system == "presidio-gliner":
            packages.extend(["gliner", "torch", "transformers"])
        if args.anonymize:
            packages.append("presidio-anonymizer")
    setup = time.perf_counter() - start
    setup_rss = peak_rss_mib()
    run({"passage": "Alice visited Boston.", "ground_truth_label": "PERSON"})
    timings = []
    for repeat in range(args.repeats):
        records = []
        started = time.perf_counter()
        with (args.output / f"predictions-{repeat + 1}.jsonl").open("w") as out:
            for i, row in enumerate(rows):
                tick = time.perf_counter()
                predictions = run(row)
                elapsed = time.perf_counter() - tick
                metrics = target_metrics(row, predictions)
                shared_type = MAPPING.get(row["ground_truth_label"])
                shared_predictions = ([p for p in predictions if p[2] == shared_type]
                                      if args.system == "presidio" else predictions)
                record = {"uuid": row["uuid"], "topic": row["topic"], "label": row["ground_truth_label"],
                          "useful": row["useful"], "mapped_presidio_type": shared_type,
                          "target_start": row["entity_start"], "target_end": row["entity_end"],
                          "seconds": elapsed, "predictions": predictions,
                          **metrics, "shared_metrics": target_metrics(row, shared_predictions)}
                records.append(record)
                out.write(json.dumps(record) + "\n")
                out.flush()
                if (i + 1) % 100 == 0:
                    print(f"{args.system} pass {repeat + 1}: {i + 1}/{len(rows)}", flush=True)
        timings.append(time.perf_counter() - started)
    useful = [r for r in records if r["useful"]]
    shared = [r for r in useful if r["mapped_presidio_type"]]
    median = statistics.median(timings)
    result = {"normalization": "remove asterisk emphasis markers; adjust gold offsets for both tools",
              "normalized_documents": normalized_count, "dataset": "deepanwa/QIB", "revision": REVISION, "sha256": hashlib.sha256(raw).hexdigest(),
              "operation": "detection + placeholder replacement" if args.system == "zink" or args.anonymize else "detection only",
              "system": args.system, "python": platform.python_version(), "platform": platform.platform(),
              "versions": {name: version(name) for name in packages},
              "zink_prompt": "ground_truth_label lowercased, underscores replaced with spaces; one label per passage",
              "presidio_configuration": ("GLiNERRecognizer; urchade/gliner_multi_pii-v1; en_core_web_sm; SpacyRecognizer removed; flat_ner=False; multi_label=True; default threshold=0.30; default chunk_size=250/overlap=50; PyTorch CPU; one annotation-derived prompt per passage"
                                         if args.system == "presidio-gliner" else "all default supported English entities; spaCy en_core_web_lg; score_threshold=0.0"),
              "mapping": MAPPING, "label_counts": dict(Counter(r["label"] for r in records)),
              "all_records": summarize(records), "useful_records": summarize(useful),
              "shared_useful_records": summarize([r["shared_metrics"] for r in shared]),
              "outside_shared_useful_records": summarize([r for r in useful if not r["mapped_presidio_type"]]),
              "by_topic_useful": {topic: summarize([r for r in useful if r["topic"] == topic]) for topic in grouped},
              "setup_seconds": setup, "baseline_peak_rss_mib": baseline, "setup_peak_rss_mib": setup_rss,
              "process_peak_rss_mib": peak_rss_mib(), "repeats": args.repeats,
              "seconds_per_corpus": timings, "median_seconds": median,
              "documents_per_second": len(rows) / median,
              "median_document_seconds": statistics.median(r["seconds"] for r in records),
              "sum_inference_seconds_last_pass": sum(r["seconds"] for r in records)}
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"system": args.system, "useful": result["useful_records"], "seconds": timings}), flush=True)


if __name__ == "__main__":
    main()
