"""Render comparison tables from saved QIB results without rerunning models."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    paths = {"Zink": ROOT / "qib-zink", "Presidio GLiNER": ROOT / "qib-presidio-gliner",
             "Presidio spaCy + anonymizer": ROOT / "qib-presidio-redaction"}
    results = {name: json.loads((path / "results.json").read_text()) for name, path in paths.items()}
    if len({r["sha256"] for r in results.values()}) != 1:
        raise ValueError("Results must use identical corpus bytes")
    if len({r.get("normalization") for r in results.values()}) != 1:
        raise ValueError("Results must use identical preprocessing")
    consistency = {}
    for name, path in paths.items():
        predictions = []
        for filename in sorted(path.glob("predictions-*.jsonl")):
            predictions.append([(r["uuid"], r["predictions"]) for r in
                                (json.loads(line) for line in filename.read_text().splitlines())])
        consistency[name] = (all(pass_predictions == predictions[0] for pass_predictions in predictions)
                             if len(predictions) > 1 else "not measured (one pass)")
    z, p, pa = results.values()
    def rate(result, group, metric):
        row = result[group]
        return f'{row[metric + "_count"]}/{row["documents"]} ({row[metric + "_rate"]:.1%})'
    def sampled_rss(path):
        samples = [json.loads(line)["resident_mib"] for line in
                   (path / "inference-rss-samples.jsonl").read_text().splitlines()]
        return statistics.median(samples)
    table = [
        ["QIB exact target-span detection (useful)", rate(z, "useful_records", "exact"), rate(p, "useful_records", "exact")],
        ["Full QIB exact detection (all 1,750 records)", rate(z, "all_records", "exact"), rate(p, "all_records", "exact")],
        ["QIB complete target coverage (useful)", rate(z, "useful_records", "fully_covered"), rate(p, "useful_records", "fully_covered")],
        ["Conservative PERSON/LOCATION-like subset: exact detection", rate(z, "shared_useful_records", "exact"), rate(p, "shared_useful_records", "exact")],
        ["Conservative PERSON/LOCATION-like subset: complete coverage", rate(z, "shared_useful_records", "fully_covered"), rate(p, "shared_useful_records", "fully_covered")],
        ["Other QIB semantic types: complete coverage", rate(z, "outside_shared_useful_records", "fully_covered"), rate(p, "outside_shared_useful_records", "fully_covered")],
        ["Detection + placeholder replacement, full-corpus time", f'{z["median_seconds"]:.2f} s', f'{p["median_seconds"]:.2f} s'],
        ["Detection + replacement throughput", f'{z["documents_per_second"]:.2f} passages/s', f'{p["documents_per_second"]:.2f} passages/s'],
        ["Median per-passage inference + replacement latency", f'{z["median_document_seconds"] * 1000:.1f} ms', f'{p["median_document_seconds"] * 1000:.1f} ms'],
        ["Extraction passes / chunks", "Two passes on the complete short passage", "One pass per 250-character chunk; 50-character overlap"],
        ["Model thresholds", "0.5 first pass; 0.9 masked second pass", "0.30 default GLiNER recognizer threshold"],
        ["Inference backend", "NuNerZero ONNX, CPU", "Recommended gliner_multi_pii-v1, PyTorch CPU"],
        ["Peak process RSS, detection + replacement", f'{z["process_peak_rss_mib"]:.0f} MiB', f'{p["process_peak_rss_mib"]:.0f} MiB'],
        ["Sampled inference RSS, median", f'{sampled_rss(paths["Zink"]):.0f} MiB', f'{sampled_rss(paths["Presidio GLiNER"]):.0f} MiB'],
        ["Cached setup, detection + replacement", f'{z["setup_seconds"]:.2f} s', f'{p["setup_seconds"]:.2f} s'],
        ["Zero-shot arbitrary-label detection", "Default GLiNER/NuNerZero workflow", "Yes, tested recommended GLiNER recognizer/model"],
        ["User input for this QIB run", "One annotation-derived semantic label per passage", "Same annotation-derived semantic label per passage"],
        ["Plain redaction / placeholders", "Built-in redact API", "Separate anonymizer package"],
        ["Fixed user replacement values", "Built-in replace_with_my_data API", "Built-in replace operator in anonymizer"],
        ["Synthetic replacement", "Built-in Faker / category-data workflow", "Custom function, e.g. Faker"],
        ["Persistent numbered placeholders", "Built-in JSON mapping workflow", "Custom mapping operator; application persists mappings"],
        ["Mask / hash / encrypt", "No corresponding public built-in operators", "Built-in anonymizer operators"],
        ["CPU installation", "zink[cpu]", "presidio-analyzer[gliner] + small spaCy model + presidio-anonymizer"],
        ["Default tested model download", "About 1.86 GB repository files", "1,155,905,399-byte GLiNER snapshot + 12.2 MiB spaCy wheel; tokenizer/config assets extra"],
        ["Installed model storage observed", "1,860,968,687 cached bytes", "1,155,905,399-byte GLiNER snapshot plus small spaCy and dependent assets"],
        ["Local inference after download", "Yes", "Yes for tested local GLiNER configuration"],
    ]
    lines = ["## Comparison table from the complete QIB runs", "",
             "Quality uses 1,734 useful records; speed processes all 1,750 passages,",
             f'with {z["repeats"]} Zink pass(es) and {p["repeats"]} Presidio pass(es) on the recorded Apple M3 CPU environment.',
             "Presidio accuracy below uses the GLiNER model recommended in its integration guide.",
             "Both receive the same annotation-assisted semantic label; neither receives the target value or offsets.", "",
             "| Aspect | Zink | Presidio + recommended GLiNER |", "| --- | --- | --- |"]
    lines.extend("| " + " | ".join(row) + " |" for row in table)
    lines.extend(["", "The full-corpus timing includes evaluation and JSONL writing. Per-passage latency",
                  "times only the tool call. Peak memory includes imports and initialization spikes.",
                  "Both timings include placeholder replacement; no synthetic values or",
                  "persistent mappings are timed. Detection coverage metrics ignore predicted labels",
                  "in the primary GLiNER comparison. The shared subset uses identical supplied semantic labels.",
                  "This remains a comparison of specific configurations, not a universal ranking.", "",
                  "Within-run prediction consistency (one pass is insufficient to test stability): " + "; ".join(f"{name}: {value}" for name, value in consistency.items()) + ".", "",
                  "## Supplementary spaCy/rule baseline", "",
                  f'Presidio with en_core_web_lg and default recognizers achieved {pa["useful_records"]["exact_rate"]:.1%} exact target detection and {pa["useful_records"]["fully_covered_rate"]:.1%} full coverage on useful records. Detection plus placeholder replacement took a median {pa["median_seconds"]:.2f} s for all 1,750 passages across three passes; peak RSS was {pa["process_peak_rss_mib"]:.0f} MiB. This is a separate non-zero-shot configuration, not the primary comparison.', "",
                  "## Per-topic target detection (useful records)", "",
                  "| QIB topic | n | Zink exact | Presidio exact | Zink complete coverage | Presidio complete coverage |",
                  "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for topic, row in z["by_topic_useful"].items():
        other = p["by_topic_useful"][topic]
        lines.append(f'| {topic} | {row["documents"]} | {row["exact_rate"]:.1%} | {other["exact_rate"]:.1%} | {row["fully_covered_rate"]:.1%} | {other["fully_covered_rate"]:.1%} |')
    path = ROOT / "QIB-COMPARISON.md"
    content = path.read_text().split("## Comparison table from the complete QIB runs")[0]
    path.write_text(content + "\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
