# Zink and Presidio: setup and initial comparison

For the full QIB evaluation and feature comparison table, see
[QIB-COMPARISON.md](QIB-COMPARISON.md). The six-document results here are only
smoke checks, not the primary quality comparison.

This report records the October 1, 2026 local run. It accompanies
`compare_presidio.py`, `smoke.jsonl`, and `smoke-results.json`. The tested Zink
checkout contains the pyOpenSci follow-up changes but still declares version
0.7.0. The environment was an existing development virtual environment, not a
fresh machine. Installation and startup observations must be read in that context.

## What was installed

| Item | Zink | Presidio configuration tested |
| --- | --- | --- |
| Package | Local Zink checkout, version 0.7.0 | `presidio-analyzer` 2.2.364 |
| Inference components | GLiNER 0.2.29, ONNX Runtime 1.30.0 | spaCy 3.8.16, `en_core_web_lg` 3.8.0 |
| Model | `deepanwa/NuNerZero_onnx` | spaCy English large pipeline |
| Hardware path | CPU, macOS ARM64 | CPU, macOS ARM64 |
| Python | 3.13.13 | Same environment |
| Labels evaluated | `person`, `location`, `date` | `PERSON`, `LOCATION`, `DATE_TIME` |
| Output operation | Detection, merge and redaction | Detection only |

Presidio also supports a GLiNER recognizer for zero-shot entity detection and
custom anonymizer operators; see the current feature table in QIB-COMPARISON.md.
Presidio has other NLP backends and custom recognizers. This report describes
one explicit configuration. The initial smoke run did not install or time
`presidio-anonymizer`. The later QIB report tests replacement operators and
records detection-plus-placeholder-replacement timing.

## Reproducing the environment

From the repository root, use a dedicated environment for future measurements:

```sh
uv venv .venv-comparison --python 3.13
uv pip install --python .venv-comparison/bin/python -e '.[cpu]' \
  'gliner==0.2.29' 'onnxruntime==1.30.0' \
  'presidio-analyzer==2.2.364' 'spacy==3.8.16'
uv pip install --python .venv-comparison/bin/python \
  'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl'
.venv-comparison/bin/python benchmarks/compare_presidio.py \
  benchmarks/smoke.jsonl /tmp/zink-new-run.json --system zink
.venv-comparison/bin/python benchmarks/compare_presidio.py \
  benchmarks/smoke.jsonl /tmp/presidio-new-run.json --system presidio
```

On Windows, use the environment's `Scripts/python.exe`. The runner refuses to
replace an existing results file; choose a new filename for each run. Save a
complete dependency lock for published experiments. The version pins above
cover the main components, not every transitive dependency or model revision.

For users installing Zink from PyPI, `pip install 'zink[cpu]'` installs GLiNER
and ONNX Runtime. Bare `pip install zink` installs the base package; it does
not enable model inference. The follow-up change warns about this on import.
`zink[gpu]` selects ONNX Runtime GPU instead, requiring a compatible GPU
runtime. GPU installation and performance were not tested here.

## Downloads and disk space

Zink's model repository lists approximately **1.86 GB**, including a roughly
1.85 GB ONNX file. Budget about **2 GB for model files**, plus package downloads,
installed dependencies and caches. The first import with a backend installed
fetches the model through Hugging Face and initializes it. Later imports reuse
the Hugging Face cache but still load the model into memory. Download and test
an import before moving offline.

Source: [NuNerZero ONNX files](https://huggingface.co/deepanwa/NuNerZero_onnx/tree/main).
Model sizes can change with repository revisions.

The spaCy wheel download in this session was **382.1 MiB**. The model is
installed into the Python environment; loading the configured Presidio analyzer
loads that pipeline. The wheel's compressed transfer size is not installed disk
usage. We explicitly installed it before running the comparison, so the runner
did not need to obtain the spaCy model during setup.

The dependency installation also downloaded Torch (121.4 MiB), ONNX Runtime
(20.5 MiB), Transformers (11.5 MiB), spaCy (6.2 MiB) and other packages. These
are observed wheel download sizes for this platform. Zink's ONNX workflow still
uses GLiNER, whose dependencies include Torch and Transformers. Package caches
and already-installed dependencies make total installation cost vary.

We did not measure aggregate transferred bytes, peak RAM, installed disk usage,
or fresh-machine download duration. Do not infer those from the model sizes.

## Initialization and API setup

Zink initializes a shared default extractor during `import zink`. With inference
dependencies present, that import can trigger network access and model loading.
The simplest call is:

```python
import zink
result = zink.redact(text, categories=("person", "location", "date"))
print(result.anonymized_text)
```

The result also contains source text and replacement details. Writing only the
transformed text avoids publishing those fields. Numbered placeholders store
source values in `~/.zink/mapping.json`; their setup and privacy properties are
outside this benchmark.

Presidio's tested setup explicitly selects the spaCy engine and model:

```python
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

engine = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
}).create_engine()
analyzer = AnalyzerEngine(nlp_engine=engine, supported_languages=["en"])
spans = analyzer.analyze(
    text=text, language="en",
    entities=["PERSON", "LOCATION", "DATE_TIME"], score_threshold=0.0,
)
```

Presidio returns typed spans and scores. Turning them into anonymized text would
require a replacement step, such as its anonymizer package. Its built-in entity
list and NLP backend configuration are documented in
[supported entities](https://microsoft.github.io/presidio/supported_entities/) and
[NLP model configuration](https://microsoft.github.io/presidio/analyzer/customizing_nlp_models/).

## What happened while getting this run working

1. The development environment initially lacked GLiNER, ONNX Runtime, Presidio,
   spaCy and pytest. They were installed successfully with `uv pip install`.
2. The first attempt to install the spaCy model encountered a sandbox restriction
   writing the uv cache. Running with approved cache/network access succeeded.
   This was an execution-environment permission issue, not a Presidio failure.
3. Zink produced upstream Torch, Hugging Face and Transformers warnings during
   initialization. They did not prevent the smoke comparison from completing.
   An ONNX Runtime telemetry cache warning also appeared in the restricted run.
4. The initial comparison completed and wrote its report. A repeat using the
   same output filename refused to overwrite it, as intended.
5. No GLiNER dummy-weight-file workaround was needed in this local environment.
   Zink's existing CI still includes its historical model-setup workaround.

The Zink follow-up removes process-wide warning suppression. Upstream warnings
are consequently visible; they should be evaluated individually rather than
silencing warnings for every library in the application.

## Accuracy protocol and results

The corpus is six hand-authored fictional English documents with **11 gold
entities** and **two documents with no entities**. Both systems receive the same
texts and the same three semantic entity types. A prediction is correct only if
its document, label, start and end offsets exactly match the annotation. A wrong
boundary or label counts as both a false positive and a false negative.
Duplicate spans with the same label are removed before scoring.

| Metric | Zink | Presidio |
| --- | ---: | ---: |
| True positives | 11 | 11 |
| False positives | 1 | 0 |
| False negatives | 0 | 0 |
| Micro precision | 0.9167 | 1.0000 |
| Micro recall | 1.0000 | 1.0000 |
| Micro F4 | 0.9947 | 1.0000 |

F4 weights recall more strongly than precision. These results validate the
runner on simple examples; **they do not establish that either system is better
on research text**. There is no confidence interval, independent annotation,
clinical corpus, multilingual assessment, or domain-shift evaluation here.
Zink's earlier README QIB results use a different evaluation and are not
comparable to these exact-span scores.

Zink retains its built-in 0.5 first-pass and 0.9 masked second-pass thresholds.
Presidio uses an explicit 0.0 analyzer threshold with its default recognizers.
Scores from different models are not calibrated; identical numeric thresholds
would not necessarily produce comparable operating points.

## Speed and memory: separate-process measurements

Each system was loaded in its own process, using cached model files. Setup now
includes imports plus model/analyzer initialization for both tools. Five warmed
passes over the same six-document corpus were measured, with Zink extraction
caching disabled. Accuracy remained the same as in the initial run.

| Measurement | Zink | Presidio |
| --- | ---: | ---: |
| Cached setup including imports | 6.86 s | 10.26 s |
| Median six-document processing | 2.685 s | 0.0570 s |
| Minimum–maximum corpus time | 2.202–3.767 s | 0.0567–0.0607 s |
| Documents per second, from median | 2.23 | 105.26 |
| Characters per second, from median | 104.27 | 4,912.20 |
| Process peak RSS after setup | 4,164.59 MiB | 1,052.61 MiB |
| Process peak RSS over full run | 4,164.59 MiB | 1,055.28 MiB |
| Process baseline high-water RSS | 25.33 MiB | 25.33 MiB |

Raw reports: `zink-isolated-results.json` and `presidio-isolated-results.json`.
RSS is measured with Unix `resource.getrusage(RUSAGE_SELF).ru_maxrss`, converted
from bytes on macOS and KiB on Linux. It includes Python, libraries, model
weights, native allocations and initialization spikes. It is a **process high
water mark**, not current/steady-state memory, GPU VRAM, incremental model size,
or total system memory. The runner returns null where `resource` is unavailable.

Zink's measured path includes merge and redaction; Presidio's is analysis only.
Consequently these numbers do not establish an equivalent end-to-end speed
ranking. The repeated run occurred in a normal development session; background
load and overlapping setup work were not controlled. For a published benchmark,
repeat sequentially on an otherwise idle machine, capture hardware details and
thread settings, and use a larger corpus with representative document lengths.

The earlier combined-process run is retained in `smoke-results.json` as an
initial workflow record. Its startup times used different boundaries and must
not be mixed with this table. Neither experiment measured first-time download
latency or installed disk usage. Cached startup can vary significantly between
processes because of file caches, imports and background load.

## Next substantive evaluation

Use a larger held-out corpus with independently reviewed span annotations and
negative examples. Record provenance, license, domain, document lengths, entity
frequencies, annotation rules, and treatment of overlapping entities. Include
per-label scores and false-positive/false-negative analysis. Keep the shared-label
comparison separate from arbitrary-label coverage: Presidio's default recognizers
do not cover every QIB category, though custom recognizers can extend them.

Freeze the environment and model revisions, run multiple timing repetitions on
the same hardware, separate installation/download/cold startup/warm inference,
and measure both analysis-only and equivalent redaction pipelines. Keep raw
sensitive corpus text and mappings out of public result artifacts.
