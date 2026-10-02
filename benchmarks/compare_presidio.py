"""Compare entity spans on a JSONL corpus; see README.md for the protocol."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import statistics
import sys
import time
from pathlib import Path

LABELS = {"person": "PERSON", "location": "LOCATION", "date": "DATE_TIME"}


def score(gold, predicted):
    """Micro exact-span-and-label scoring; duplicates count only once."""
    tp = len(gold & predicted)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f4 = 17 * precision * recall / (16 * precision + recall) if precision + recall else 0.0
    return dict(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall, f4=f4)


def peak_rss_mib():
    """Process high-water resident memory, including model initialization."""
    try:
        import resource
    except ImportError:
        return None
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss / (1024 * 1024 if sys.platform == "darwin" else 1024)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--system", choices=["zink", "presidio"], required=True,
                        help="Run each system in a separate process for peak RSS")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    raw = args.corpus.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Corpus must contain at least one document")
    gold = set()
    for i, row in enumerate(rows):
        for entity in row["entities"]:
            start, end, label = entity["start"], entity["end"], entity["label"]
            if label not in LABELS or not 0 <= start < end <= len(row["text"]):
                raise ValueError(f"Invalid entity in document {i}")
            gold.add((i, start, end, label))

    baseline_rss = peak_rss_mib()
    started = time.perf_counter()
    if args.system == "zink":
        import zink
        def run(text):
            return [(r.start, r.end, r.label) for r in zink.redact(
                text, categories=tuple(LABELS), use_cache=False, auto_parallel=False,
            ).replacements]
        packages = ["zink", "gliner", "onnxruntime", "torch", "transformers"]
    else:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        engine = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        }).create_engine()
        analyzer = AnalyzerEngine(nlp_engine=engine, supported_languages=["en"])
        reverse = {value: key for key, value in LABELS.items()}
        def run(text):
            return [(r.start, r.end, reverse[r.entity_type]) for r in analyzer.analyze(
                text=text, language="en", entities=list(LABELS.values()), score_threshold=0.0,
            )]
        packages = ["presidio-analyzer", "spacy", "en-core-web-lg"]
    setup_seconds = time.perf_counter() - started
    setup_rss = peak_rss_mib()
    result = {"python": platform.python_version(), "platform": platform.platform(),
              "corpus_sha256": hashlib.sha256(raw).hexdigest(), "documents": len(rows),
              "versions": {name: importlib.metadata.version(name) for name in packages},
              "system": args.system, "repeats": args.repeats,
              "setup_seconds": setup_seconds,
              "baseline_peak_rss_mib": baseline_rss,
              "setup_peak_rss_mib": setup_rss}
    run("Alice visited Boston on June 12, 2025.")  # unmeasured warmup
    timings = []
    for _ in range(args.repeats):
        predicted = set()
        started = time.perf_counter()
        for i, row in enumerate(rows):
            predicted.update((i, start, end, label) for start, end, label in run(row["text"]))
        timings.append(time.perf_counter() - started)
    median = statistics.median(timings)
    result["results"] = {**score(gold, predicted), "seconds_per_corpus": timings,
                         "median_seconds": median, "min_seconds": min(timings),
                         "max_seconds": max(timings),
                         "documents_per_second": len(rows) / median,
                         "characters_per_second": sum(len(row["text"]) for row in rows) / median,
                         "process_peak_rss_mib": peak_rss_mib()}
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
