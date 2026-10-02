# Zink–Presidio comparison

The main accuracy evaluation now uses [QIB](QIB-COMPARISON.md), comparing
Zink's NuNerZero ONNX workflow with the GLiNER model in Presidio's official
integration example. Both receive the same semantic prompts. The spaCy/rule
configuration is retained as a supplementary baseline.
The smoke results below only validate the original runner.

See [COMPARISON.md](COMPARISON.md) for installation, downloads, setup,
troubleshooting, accuracy, repeated speed measurements and peak process memory.

This runner compares detection on identical English texts for shared labels:
`person` → `PERSON`, `location` → `LOCATION`, and `date` → `DATE_TIME`.
Presidio uses its built-in recognizers and spaCy `en_core_web_lg`; Zink uses
its default NuNerZero ONNX model and normal two-pass label-chunk extraction.
Presidio's score threshold is explicitly 0.0; Zink retains its built-in 0.5/0.9
thresholds. These scores are not calibrated across models. No custom recognizers
are added. This compares these configurations, not every possible configuration.

```sh
uv pip install --python .venv/bin/python -e '.[cpu]' presidio-analyzer
uv pip install --python .venv/bin/python 'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl'
.venv/bin/python benchmarks/compare_presidio.py benchmarks/smoke.jsonl /tmp/zink-smoke.json --system zink
.venv/bin/python benchmarks/compare_presidio.py benchmarks/smoke.jsonl /tmp/presidio-smoke.json --system presidio
```

The first run downloads models (about 2 GB for Zink, plus spaCy). Run on CPU
with sufficient memory. Output records installed versions, platform, corpus
SHA-256, setup time, warmed inference time and documents per second. Setup includes imports and model initialization and is
reported separately; it depends on cache state and is not a cold-start benchmark.
Timing includes Zink's redaction pipeline but only Presidio's analyzer, so it is
not an equivalent end-to-end anonymization speed comparison. The runner measures five warmed passes by default (`--repeats`).
Run each system in its own process with `--system`; peak RSS includes setup
spikes and is available on Unix. Use the same hardware for timing claims. Zink extraction caching is disabled.

JSONL documents have `text` and `entities` with Python character offsets
(`start` inclusive, `end` exclusive) and a shared `label`. Predictions are
matched exactly by document, start, end and label, with duplicates removed.
Micro precision, recall, F4, TP, FP and FN are reported. Boundary differences
count as both FP and FN. Documents without entities test false positives.
No source text or predictions are included in the output report.

`smoke.jsonl` contains six hand-authored fictional examples, including two
negative examples. It validates the workflow; it is too small and simple to
establish comparative quality or clinical/interview performance. It does not
reproduce the earlier QIB results. For a substantive comparison, supply a larger,
independently annotated held-out corpus using this schema and report its
provenance, license, annotation policy, label distribution and limitations.
Keep model revisions and an environment lock alongside published results.

Presidio can be extended to other labels; its default labels do not cover all
35 QIB categories. A QIB-wide comparison without documenting recognizer coverage
would conflate unsupported labels with failed detections. See the
[Presidio supported entities](https://microsoft.github.io/presidio/supported_entities/)
and [NLP model configuration](https://microsoft.github.io/presidio/analyzer/customizing_nlp_models/).

## Recorded smoke run

See `smoke-results.json` for the environment and corpus hash. On the six
fictional documents (11 gold entities), Zink found all 11 with one extra
prediction (precision 0.9167, recall 1.0); Presidio found all 11 with no extra
prediction. These are workflow-validation results only. Single-run warmed time
was 2.60 s for Zink's redaction pipeline and 0.086 s for Presidio's analyzer;
the timing boundaries differ as described above. Neither result establishes
performance on real research text.
