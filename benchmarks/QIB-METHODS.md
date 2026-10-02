# Zink versus Presidio on QIB

We created [QIB](https://huggingface.co/datasets/deepanwa/QIB) to address the
lack of diverse benchmarks for quasi-identifier detection. The primary comparison
uses Zink and Presidio with GLiNER; the spaCy/rule run is supplementary.

## Corpus and reproducibility

Pinned dataset revision: `af345705a03852b8bd77c2e69c971a0361b1e71d`.
File: `qib_validated_with_indices_filtered_useful.json`.
It contains 1,750 passages across 35 topics, 1,734 marked useful and 16 marked
not useful. All target strings exactly match the supplied character offsets. Passage lengths
range from 131 to 355 characters (median 193), or 24 to 58 whitespace-separated
words (median 33).
The filename does not mean every record has `useful: true`. The report includes
both sets; useful records are the primary quality result.

Run these commands sequentially from the repository root in a Python environment:

```sh
python -m pip install -e '.[cpu]' 'presidio-analyzer[gliner]==2.2.364' 'presidio-anonymizer==2.2.364'
python -m pip install 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl'
python benchmarks/qib_presidio.py --system zink --output /tmp/qib-zink-new --repeats 1
python benchmarks/qib_presidio.py --system presidio-gliner --anonymize --output /tmp/qib-presidio-gliner-new --repeats 1
```

Choose new output directories for each run. Each contains the downloaded corpus,
per-record predictions and `results.json`, including F4, precision, recall, TP,
FP and FN. The pinned dataset is validated before and after preprocessing.
The recorded dependency versions are in [qib-environment-freeze.txt](qib-environment-freeze.txt).
Zink's recorded model revision appears below; its loader follows the model's
main branch, so future runs can use newer assets unless that revision is pinned.

To recompute scores from the committed predictions without downloading models
or rerunning inference:

```sh
python benchmarks/qib_presidio.py --rescore benchmarks/qib-zink
python benchmarks/qib_presidio.py --rescore benchmarks/qib-presidio-gliner
python benchmarks/render_qib_report.py
```

Rescoring updates quality fields in `results.json` from the last recorded pass,
matching the runner's summary convention. Predictions and timing measurements
remain unchanged. The renderer updates the detailed tables below.

## Common formatting normalization

102 source passages contain paired asterisks used for emphasis. Zink interprets
`*...*` as exclusion syntax and removes the markers, shifting source offsets.
The final comparison therefore removes all asterisks from both systems' input
and updates the gold offsets and target strings consistently. This transformation
uses only the source text, not a target-specific recognition rule. Offsets are
validated both before and after normalization. Initial unnormalized runs were
quarantined and are not used as final evidence.

## Presidio download and setup measurements

The extra uses GLiNER in addition to Presidio. The small spaCy wheel download
was 12.2 MiB. Prefetching the pinned GLiNER model downloaded a snapshot containing
1,155,905,399 bytes in 36.48 seconds on this connection. This measures only the
snapshot fetch, not package installation, dependent tokenizer/config downloads,
model initialization, or the end-to-end first call. The measured first setup
and later cached setup are recorded separately when available.
See `presidio-gliner-download.json`. The first integration check after that
prefetch took 16.99 s for imports and model/analyzer setup; it was an existing
development environment, not a clean-machine installation. The full primary
run's subsequent cached setup took 14.82 s.
See `presidio-gliner-first-setup.json`.

## Detection protocols

**Zink:** one semantic label per passage, derived from `ground_truth_label` by
lowercasing and replacing underscores with spaces. For example, `MOVIE_TITLE`
becomes `movie title`. This is **annotation-assisted label selection**: the system
is told the target type, but never receives the target value or offsets. It is
not a blind scan of an unknown document and is not a reproduction of the older
README `zink_human` results. Uses the ordinary redaction API, built-in two-pass
thresholds (0.5 and 0.9), no extraction cache, no document chunking.

**Presidio + GLiNER (primary comparison):** follows the official GLiNER example's
model `urchade/gliner_multi_pii-v1`, PyTorch CPU backend, small spaCy pipeline,
removal of `SpacyRecognizer`, `flat_ner=False` and `multi_label=True`. Uses the
recognizer defaults: threshold 0.30 and 250-character chunks with 50-character
overlap. Model revision is pinned to `1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d`.
The mapping is extended to register QIB labels; before each sequential call,
the recognizer's prompt list is set to the same single semantic label supplied
to Zink. The target value and offsets are never supplied. Presidio's analyzer
threshold is 0.0 so it does not add a second filter over the model threshold.
This keeps both systems zero-shot and gives them the same label information,
while retaining their respective models and extraction implementations.
Placeholder replacement is included using `presidio-anonymizer`.

The documented example originally maps four generic prompts. Restricting its
prompt list to one QIB semantic type per record is an explicit benchmark
adaptation, not a claim that the documentation ships a ready-made QIB scanner.
Default pattern recognizers remain registered but QIB requests select only
the target's registered entity ID; spaCy's recognizer is removed. The small
spaCy pipeline still supplies NLP artifacts, as in the official example.
[Official integration example](https://presidio.dataprivacystack.org/samples/python/gliner/).

**Presidio baseline:** spaCy `en_core_web_lg` plus all default supported English
recognizers, analyzer threshold 0.0. It scans all supported types, giving it the
opportunity to detect a QIB target incidentally even when there is no direct
semantic mapping. No QIB-specific recognizers or gold values are supplied.

The primary zero-shot comparison uses identical label information with each
tool’s respective model and extraction configuration. The supplementary
spaCy/rule baseline uses different label information. For the spaCy/rule baseline, the full-corpus result captures both detection and
category coverage. That baseline is retained separately from the primary
Zink-versus-Presidio-GLiNER comparison.
For the supplementary spaCy/rule baseline, a conservative shared-label result
restricts Presidio predictions to
`PERSON` or `LOCATION` for QIB labels that map to those types. The frozen mapping
is included in the JSON output. Ambiguous categories such as fictional characters,
pet names, venues and street names are excluded from the conservative mapping.

## What accuracy means here

The main comparison reports micro-averaged F4, precision and recall across the
1,734 useful records. Each passage has one annotated target. We compare character
boundaries, ignoring predicted label names, and deduplicate identical spans.

- **TP:** a predicted span matches both target boundaries.
- **FP:** a predicted span does not match the target boundaries.
- **FN:** no prediction matches the target boundaries.
- **Precision:** TP / (TP + FP).
- **Recall:** TP / (TP + FN).
- **F4:** 17TP / (17TP + 16FN + FP).

A boundary mismatch counts as both an FP and an FN. Zero-denominator scores are
reported as zero. F4 emphasizes recall because missed identifiers can leave
sensitive information exposed. These scores assess detection against the QIB
annotations; placeholder replacement is included in the timing.

Exact-span rates, full character coverage and overlap remain supplementary
metrics below. Coverage allows broader or adjacent predicted spans. The historical
README results use a separate protocol and are not reproduced by this run.

## Zero-shot detection and replacements

The tested Presidio spaCy/rule baseline does not accept arbitrary semantic labels
as zero-shot prompts. It uses trained NER categories and configured recognizers.
**The primary Presidio run uses GLiNER** through `GLiNERRecognizer` with the
documented PyTorch setup. The recognizer also supports ONNX when an appropriate
model asset is available. Different backends and models can change accuracy,
speed and memory.
Calling Presidio universally non-zero-shot would be incorrect.
[Official GLiNER integration](https://presidio.dataprivacystack.org/samples/python/gliner/).

Presidio's separate `presidio-anonymizer` package supports placeholders, fixed
values, removal, masking, hashing, encryption and custom functions. Faker can be
used in a custom operator, and its pseudonymization example demonstrates stable
mapping and restoration. Users own persistence of that mapping; Zink exposes a
built-in persistent numbered-placeholder workflow.
[Anonymizer operators](https://presidio.dataprivacystack.org/anonymizer/),
[pseudonymization sample](https://presidio.dataprivacystack.org/samples/python/pseudonymization/).

Local replacement verification with Presidio Anonymizer 2.2.364 confirmed default
placeholders, fixed per-label values and Faker custom functions. See
`presidio-replacement-check.json`. These checks use known spans and do not imply
any detector accuracy. The anonymizer installation added a 7.6 MiB cryptography
wheel in this environment, plus cffi and pycparser.

## Speed and memory protocol

Each tool runs in its own process on CPU. Models are cached. Setup includes
imports and model initialization, excluding package installation and the QIB
fetch. After warmup, one full Zink pass and one full Presidio-GLiNER pass are measured. The separate
spaCy/rule baseline uses three full passes. Zink
full-corpus speed is consequently a single-run observation; the primary GLiNER comparison also uses a single full-pass timing. Baseline
spaCy/rule timing uses the median of three passes. Timing includes span scoring
and JSONL output; per-document inference timers are recorded separately. Peak RSS
includes Python, native libraries and initialization spikes. It is a process high
water mark, not steady-state memory or GPU VRAM. A separate `ps` observer samples
resident memory during each primary tool’s inference phase at one-second intervals. Those
samples are observational active-memory figures, not an isolated steady-state
allocation measurement. The observer starts after model initialization.

The primary comparison times detection plus placeholder replacement for both
systems. The supplementary Presidio spaCy/rule analysis-only run uses detection only.
Its throughput cannot be labeled equivalent end-to-end redaction throughput.
Short QIB passages and one prompted label also differ from multi-label and
long-document workloads. No fixed runtime thread limits were applied.

## Why the earlier speed result was plausible

The smoke run took about 2.7 seconds for six sentences, approximately 0.45 seconds
per sentence when averaged. That is consistent with Zink taking around a second
or less for a short sentence. It was never a 2.7-second-per-sentence measurement.
A mean over a batch also is not a latency guarantee for each individual input.

The spaCy/rule baseline performs a different recognition workload from Zink's
label-conditioned transformer and masked second pass. Zink's `predict2` performs
two `predict_entities` calls per label chunk, with chunks of two labels. More
labels therefore increase the number of model calls. QIB's Zink configuration
uses one label per passage. Presidio's other model backends, including GLiNER,
would incur different runtime costs. The selected recognition architecture is
a plausible explanation for the observed speed gap; no profiler was run to
attribute the gap quantitatively to individual operations.

A separate Presidio `--anonymize` run measures detection plus default placeholder
replacement. This is closer to Zink's redaction workload. It does not compare
Faker generation, persistent mappings, masking, encryption or remote services.

```sh
uv pip install --python .venv/bin/python 'presidio-anonymizer==2.2.364'
.venv/bin/python benchmarks/qib_presidio.py --system presidio --anonymize \
  --output /tmp/qib-presidio-redaction-new --repeats 3
```

## Environment and disk measurements

The QIB run uses an Apple M3 with 8 physical/logical CPU cores and 16 GiB RAM,
macOS ARM64, Python 3.13.13. Hardware, cached Zink model revision and directory
sizes are recorded in `qib-environment.json`; installed package versions are in
`qib-environment-freeze.txt`. The cached Zink model revision is
`40349bb15d985ced384bed5c35115fd70069f4b9`, with 1,860,968,687 cached bytes.
A future run must pin that model revision as well as dependencies to guarantee
identical assets; the current default loader follows the model repository's main.

Observed installed directory allocations (`du -sk`) were about 426.6 MiB for
`en_core_web_lg`, 555.9 MiB for Torch, 75.8 MiB for ONNX Runtime, 2.36 MiB for
GLiNER, 2.11 MiB for Presidio Analyzer and 0.35 MiB for Presidio Anonymizer.
These are component sizes, not complete fresh-environment installation footprints.
They exclude other dependencies and caches. Some libraries, including Torch,
can be imported by the tested Presidio installation too; attributing every shared
dependency exclusively to one tool would be incorrect.



## Comparison table from the complete QIB runs

Quality uses 1,734 useful records; speed processes all 1,750 passages,
with 1 Zink pass(es) and 1 Presidio pass(es) on the recorded Apple M3 CPU environment.
Presidio accuracy below uses the GLiNER model recommended in its integration guide.
Both receive the same annotation-assisted semantic label; neither receives the target value or offsets.

| Aspect | Zink | Presidio + recommended GLiNER |
| --- | --- | --- |
| F4 (useful records) | 0.8520 | 0.7906 |
| Precision (useful records) | 81.16% | 64.22% |
| Recall (useful records) | 85.47% | 80.22% |
| QIB exact target-span detection (useful) | 1482/1734 (85.5%) | 1391/1734 (80.2%) |
| Full QIB exact detection (all 1,750 records) | 1492/1750 (85.3%) | 1401/1750 (80.1%) |
| QIB complete target coverage (useful) | 1516/1734 (87.4%) | 1520/1734 (87.7%) |
| Conservative PERSON/LOCATION-like subset: exact detection | 381/503 (75.7%) | 359/503 (71.4%) |
| Conservative PERSON/LOCATION-like subset: complete coverage | 397/503 (78.9%) | 395/503 (78.5%) |
| Other QIB semantic types: complete coverage | 1119/1231 (90.9%) | 1125/1231 (91.4%) |
| Detection + placeholder replacement, full-corpus time | 782.82 s | 160.49 s |
| Detection + replacement throughput | 2.24 passages/s | 10.90 passages/s |
| Median per-passage inference + replacement latency | 442.8 ms | 92.4 ms |
| Extraction passes / chunks | Two passes on the complete short passage | One pass per 250-character chunk; 50-character overlap |
| Model thresholds | 0.5 first pass; 0.9 masked second pass | 0.30 default GLiNER recognizer threshold |
| Inference backend | NuNerZero ONNX, CPU | Recommended gliner_multi_pii-v1, PyTorch CPU |
| Peak process RSS, detection + replacement | 4193 MiB | 2885 MiB |
| Sampled inference RSS, median | 3035 MiB | 2106 MiB |
| Cached setup, detection + replacement | 6.74 s | 14.82 s |
| Zero-shot arbitrary-label detection | Default GLiNER/NuNerZero workflow | Yes, tested recommended GLiNER recognizer/model |
| User input for this QIB run | One annotation-derived semantic label per passage | Same annotation-derived semantic label per passage |
| Plain redaction / placeholders | Built-in redact API | Separate anonymizer package |
| Fixed user replacement values | Built-in replace_with_my_data API | Built-in replace operator in anonymizer |
| Synthetic replacement | Built-in Faker / category-data workflow | Custom function, e.g. Faker |
| Persistent numbered placeholders | Built-in JSON mapping workflow | Custom mapping operator; application persists mappings |
| Mask / hash / encrypt | No corresponding public built-in operators | Built-in anonymizer operators |
| CPU installation | zink[cpu] | presidio-analyzer[gliner] + small spaCy model + presidio-anonymizer |
| Default tested model download | About 1.86 GB repository files | 1,155,905,399-byte GLiNER snapshot + 12.2 MiB spaCy wheel; tokenizer/config assets extra |
| Installed model storage observed | 1,860,968,687 cached bytes | 1,155,905,399-byte GLiNER snapshot plus small spaCy and dependent assets |
| Local inference after download | Yes | Yes for tested local GLiNER configuration |

The full-corpus timing includes evaluation and JSONL writing. Per-passage latency
times only the tool call. Peak memory includes imports and initialization spikes.
Both timings include placeholder replacement; no synthetic values or
persistent mappings are timed. Detection coverage metrics ignore predicted labels
in the primary GLiNER comparison. The shared subset uses identical supplied semantic labels.
This remains a comparison of specific configurations, not a universal ranking.

Within-run prediction consistency (one pass is insufficient to test stability): Zink: not measured (one pass); Presidio GLiNER: not measured (one pass); Presidio spaCy + anonymizer: True.

## Supplementary spaCy/rule baseline

Presidio with en_core_web_lg and default recognizers achieved 44.2% exact target detection and 49.8% full coverage on useful records. Detection plus placeholder replacement took a median 19.32 s for all 1,750 passages across three passes; peak RSS was 1085 MiB. This is a separate non-zero-shot configuration, not the primary comparison.

## Per-topic target detection (useful records)

| QIB topic | n | Zink exact | Presidio exact | Zink complete coverage | Presidio complete coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mother's maiden name | 46 | 69.6% | 67.4% | 91.3% | 87.0% |
| City of birth | 49 | 95.9% | 98.0% | 95.9% | 100.0% |
| High school mascot | 50 | 92.0% | 76.0% | 92.0% | 86.0% |
| First pet's name | 50 | 94.0% | 78.0% | 96.0% | 92.0% |
| Street you grew up on | 50 | 96.0% | 100.0% | 96.0% | 100.0% |
| First car's make/model | 50 | 96.0% | 88.0% | 98.0% | 94.0% |
| Favorite childhood friend | 50 | 78.0% | 30.0% | 80.0% | 36.0% |
| City or town of first job | 50 | 92.0% | 96.0% | 92.0% | 98.0% |
| Maternal grandmother's maiden name | 49 | 87.8% | 77.6% | 91.8% | 95.9% |
| Favorite color | 49 | 77.6% | 53.1% | 87.8% | 91.8% |
| Favorite food | 50 | 84.0% | 78.0% | 92.0% | 96.0% |
| Favorite movie | 50 | 100.0% | 94.0% | 100.0% | 96.0% |
| Favorite book | 50 | 94.0% | 88.0% | 96.0% | 96.0% |
| Favorite song | 50 | 98.0% | 100.0% | 98.0% | 100.0% |
| Favorite sports team | 50 | 88.0% | 90.0% | 92.0% | 94.0% |
| Favorite artist/band | 50 | 92.0% | 82.0% | 94.0% | 86.0% |
| Favorite author | 49 | 57.1% | 65.3% | 57.1% | 65.3% |
| Dream vacation destination | 50 | 94.0% | 90.0% | 94.0% | 94.0% |
| Favorite board game/video game | 50 | 96.0% | 96.0% | 96.0% | 96.0% |
| Make and model of your first bicycle | 50 | 96.0% | 92.0% | 96.0% | 100.0% |
| What was your childhood nickname? | 50 | 100.0% | 100.0% | 100.0% | 100.0% |
| What is the name of the hospital where you were born? | 50 | 100.0% | 94.0% | 100.0% | 94.0% |
| What is the title of your favorite childhood book? | 50 | 94.0% | 90.0% | 94.0% | 96.0% |
| In what city did you meet your spouse/partner? | 50 | 98.0% | 98.0% | 98.0% | 98.0% |
| What is the name of a place you visited as a child? | 50 | 86.0% | 98.0% | 86.0% | 100.0% |
| What was the make and model of your first computer? | 50 | 100.0% | 94.0% | 100.0% | 94.0% |
| What was the last name of your favorite teacher in high school? | 50 | 10.0% | 4.0% | 12.0% | 20.0% |
| What was the name of the street of your first childhood home? | 50 | 94.0% | 96.0% | 96.0% | 98.0% |
| Who was your childhood hero? | 50 | 92.0% | 74.0% | 96.0% | 82.0% |
| What is the name of your favorite restaurant? | 49 | 93.9% | 95.9% | 95.9% | 98.0% |
| What is the title of a movie you saw in the last year? | 50 | 98.0% | 96.0% | 98.0% | 98.0% |
| What is a word that describes you best? | 49 | 75.5% | 59.2% | 75.5% | 83.7% |
| What is your favorite fictional character? | 50 | 92.0% | 94.0% | 92.0% | 94.0% |
| If you could have any superpower, what would it be? | 44 | 6.8% | 22.7% | 9.1% | 38.6% |
| What is your favorite quote? | 50 | 62.0% | 44.0% | 62.0% | 64.0% |
