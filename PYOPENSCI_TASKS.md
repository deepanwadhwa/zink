# pyOpenSci review fixes and test plan

Tracking issue: [pyOpenSci/software-submission#352](https://github.com/pyOpenSci/software-submission/issues/352).

This is an implementation checklist. Unchecked items remain to be implemented and verified. Extend the existing test suite for each behavior change; retain its real-model integration coverage.

## Execution log

- Goal active. Changes are being implemented and committed in focused increments; pushing and release publication are reserved for the completed package update.
- Original full-suite baseline, run from a clean archived checkout with isolated mapping files and the cached CPU model: **41 passed in 59.71 seconds** on Python 3.13.13, GLiNER 0.2.29, ONNX Runtime 1.30.0, macOS arm64. Model revision: `40349bb15d985ced384bed5c35115fd70069f4b9`.
- Reproduced the original substring replacement, overlapping-protection, shared-request-text, and README custom-example failures before fixes. New deterministic regressions and real-model checks are being added to the existing feature tests.
- Version `0.7.1` is the prepared patch version; historical tags will retain historical source snapshots.

## Starting point

- Inspected checkout: `4f7c41837ced05d5ef2638be07b4c95c0a62a380`, the same commit identified by reviewer 1; package version `0.7.0`.
- Baseline actually run while preparing this plan: `.venv/bin/python -m pytest tests -q` — **11 passed in 11.77 seconds**. These are optional-backend and benchmark-metric checks, not the full feature suite.
- The full `zink/tests` feature suite, model inference, Docker, builds, and multi-platform checks have not been run for this planning task. The reviewer's earlier report of 41 passing tests is historical evidence, not a new local result.
- The documentation site, API reference, advanced file tutorial, related-tools page, Presidio benchmark, and lint workflow already exist. Verify and improve these rather than recreate them.
- The reported global replacement, overlapping-protection, shared extractor state, README examples, eager model initialization, and commented-out code are visible in this checkout.
- Local tags currently stop at `v0.6.3`; check the remote before preparing releases.

## Priority and dependencies

| Order | Task | Priority | Depends on |
| --- | --- | --- | --- |
| 1 | T1: Establish test isolation and baseline | P0: foundation | None |
| 2 | T2: Replace only detected spans | P0: correctness | T1 |
| 3 | T3: Preserve overlapping protected text | P0: correctness | T1 |
| 4 | T4: Correct and exercise README examples | P0: usability | T1–T3 |
| 5 | T5: Remove shared extractor request state | P1: robustness | T1 |
| 6 | T6: Reduce import cost and defer inference setup | P1: performance | T1; coordinate with T5 |
| 7 | T7: Complete public API documentation and examples | P1: review requirements | T2–T6 |
| 8 | T8: Improve README links, comparison, and badges | P1: discoverability | T7; finalize coverage badge after T10 |
| 9 | T9: Remove dead code and unused experiments | P2: maintenance | T1; verify T2–T6 afterward |
| 10 | T10: Update Python, CI, packaging, and Docker validation | P1: compatibility | T1–T7 and T9; supplies coverage evidence for T8 |
| 11 | T11: Reconcile historical releases and prepare fixed release | P1: release tracking | Historical releases can be investigated immediately; fixed release needs T10 |
| 12 | T12: Assemble evidence and review response | P1: completion | All applicable tasks |

The reviewer explicitly calls concurrency an improvement opportunity and missing class/server docstrings a minor issue. They remain in this plan because the requested scope includes thorough feature testing. Type checking was explicitly optional in the initial editor checks; treat it as a separate follow-up, not a prerequisite for these fixes. The JOSS-only template items do not apply to the current submission.

## T1 — Establish a reliable test baseline and fixtures

Primary files: `zink/tests/test_basic.py`, `test_exclusion.py`, `test_persistent_mapping.py`, `test_shield.py`, `test_thread.py`, `test_thread2.py`; `tests/test_optional_backend.py`; `pyproject.toml`. Add a shared `conftest.py` only where fixtures are needed.

- [ ] Run and record the existing full suite before changes, with Python/backend/model versions and model revision. Record failures and environmental limitations separately.
- [ ] Keep existing real-model tests. Add deterministic tests using controlled entity spans/model responses so a detection change cannot hide a transformation bug.
- [ ] Isolate every test's mapping file and replacement-data cache in temporary directories, including `test_shield.py`, which currently uses the default mapping path. Use pytest fixtures or scoped patches; never repurpose the process's real `HOME`.
- [ ] Reset extraction caches, random stubs, and mutable global pipeline state between tests. Verify that a test cannot change another test's replacement mapping or results.
- [ ] Register an `integration` marker for tests needing the actual GLiNER/ONNX model. Do not apply model mocks globally to integration tests.
- [ ] Account for eager imports during collection: selecting `-m 'not integration'` alone cannot prevent the current import-time model initialization. Make offline collection work as part of T6; until then, use explicit, scoped subprocess/backend stubs for targeted unit checks.
- [ ] Use the existing pipeline object's extractor or extraction boundary for test doubles. The advertised custom `extractor`/`merger`/`replacer` arguments currently reach an unsupported constructor signature; do not rely on them as a working injection API.
- [ ] Use exact output, span, count, and source assertions for deterministic cases. Patch random choices for reproducibility; do not assert arbitrary Faker-generated names.
- [ ] Confirm collection includes both `tests` and `zink/tests`. Keep a runnable command for the combined suite in `CONTRIBUTING.md`.

Acceptance: fixtures leave user files untouched; model-dependent tests remain visible; deterministic checks fail for the intended bug rather than setup errors.

## T2 — Apply consistent replacements only to detected spans

Source: [reviewer 1, comment 1](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6209920390).

Primary implementation: `zink/replacer/replacer.py`; integration through `zink/pipeline.py` and the public wrappers. Extend **`zink/tests/test_basic.py`** and relevant structure checks in **`test_thread2.py`**.

- [ ] Replace global `text.replace()` with assembly from original-text offsets while retaining one replacement value for each repeated source string within a call.
- [ ] Apply values to original detected spans only. Do not search the modified output or replace newly inserted text.
- [ ] Preserve fixed-string and list-of-candidates replacements, case-insensitive label keys, and both consistency modes.
- [ ] Verify existing fallback behavior for Faker/JSON, absent or unchanged replacement values, and `source` metadata. Decide and document any discrepancy between the two replacement paths before changing it.

Add parameterized regression tests:

| Case | Required assertion |
| --- | --- |
| `Ann met Annette; Ann arrived later.`; all three name spans detected; fixed `Alice` | Exactly `Alice met Alice; Alice arrived later.` in both modes; never `Aliceette` |
| `Ann met Annette.`; only `Ann` detected | Exactly `Alice met Annette.`; undetected substring remains untouched |
| Identical text appears twice but only one occurrence is detected | Only that occurrence changes |
| Two detected names with replacements containing another source name | Inserted output is not replaced again |
| Repeated source string, candidate list, consistency on | One selection is reused across all matching detected spans |
| Candidate list, consistency off | Each span uses its controlled per-occurrence selection |
| Longer, shorter, and empty replacement strings | Later offsets still refer to the original text; preserve or explicitly validate the documented empty-string behavior |
| Unicode, multiline text, start/end boundaries, punctuation | Exact untouched text outside detected spans is preserved |
| Empty input and no detected entities | Input is unchanged; replacement count is zero |
| Cached and uncached public calls with different user mappings | Same detections, independently correct outputs; no prior-call metadata/mapping contamination |

- [ ] Exercise both `replace()` and `replace_with_my_data()`, with `ensure_consistency=True/False`, `use_cache=True/False` where available, and fixed/Faker/JSON paths.
- [ ] Assert result fields, original offsets, label/source metadata, and replacement counts in addition to output strings.
- [ ] Add a real-model smoke case for the reviewer's example, recording model detections separately from replacement correctness.

Acceptance: the exact reviewer reproduction fails before the fix and passes afterward; replacements never modify undetected characters.

## T3 — Preserve overlapping protected phrases

Source: [reviewer 1, comment 2](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6209920390).

Primary implementation: `zink/zink.py:prep`, `zink/pipeline.py:_parse_exclusions` and exclusion filtering. Extend **`zink/tests/test_exclusion.py`**; add numbered-mode checks to **`test_persistent_mapping.py`**.

- [ ] Find all protected spans against the original text, merge overlapping intervals, and insert well-formed markers once.
- [ ] Preserve original casing and characters by slicing original matches; the current substitution can impose the casing of the supplied term.
- [ ] Retain case-insensitive whole-word matching. Define expected behavior for punctuation-heavy terms, adjacent intervals, empty terms, existing markers, and unmatched literal asterisks before adjusting those cases.

Add deterministic tests for:

- [ ] `prep('Alice arrived.', ['Alice', 'Alice arrived'])` followed by redaction returns exactly `Alice arrived.`; reverse list order gives the same protection.
- [ ] Nested, partially overlapping, duplicate, and repeated phrases; no nested or doubled marker corruption.
- [ ] Protected and unprotected names in the same sentence: keep protected text, redact the other detected name.
- [ ] Duplicate phrase at different positions, mixed case, Unicode, multiple lines, and matches at text boundaries.
- [ ] Whole-word behavior: protecting `Ann` must not protect the substring in `Annette`.
- [ ] Empty protection list and absent terms preserve text; empty protection entries follow the chosen documented behavior.
- [ ] Entity fully inside, partially overlapping, and outside a protected interval: assert the current overlap-based exclusion contract and clean-text offsets.
- [ ] Cached/uncached and sequential/chunked redaction preserve equivalent protected spans, including a phrase crossing a chunk boundary.
- [ ] Numbered redaction never records a protected entity as a replacement or adds it to the persistent mapping.
- [ ] Existing manual-marker tests continue passing, including defined behavior for unmatched markers/literal asterisks.

Acceptance: protected phrases remain byte-for-byte intact after marker removal; unrelated entities are still redacted; metadata uses correct clean-text coordinates.

## T4 — Correct the README examples and run them as regressions

Source: [reviewer 1, comment 3](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6209920390).

- [ ] Change the two persistent-numbering calls from `labels=` to `categories=`.
- [ ] Change the car replacement tuple to a supported list. Supporting tuples is not required to fix this example.
- [ ] Check surrounding prose and displayed outputs against current signatures, including numbered placeholders in the shield example.
- [ ] Execute the corrected custom-replacement snippet in **`test_basic.py`**, using controlled detections and candidate choice; assert the exact final string.
- [ ] Execute the corrected numbering workflow in **`test_persistent_mapping.py`**, with a temporary mapping; assert persistence across calls, reuse by a fresh pipeline/process, and separation between different entities.
- [ ] Exercise the README shield workflow in **`test_shield.py`**: the wrapped function receives redacted values and its returned string is restored correctly.
- [ ] Keep README examples and executable tests synchronized. Prefer running the relevant actual code blocks, or shared examples used by both, rather than testing a corrected copy while the README can drift.
- [ ] Run the snippets with the real CPU backend as well. For random IDs/candidates, assert stable relationships or permitted values rather than illustrative literal outputs.

Acceptance: published examples execute without the reported `TypeError`s and demonstrate the behavior they claim.

## T5 — Remove shared request text from the extractor

Source: [reviewer 1, comment 4](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6209920390). This is a reviewer-designated improvement opportunity.

Primary implementation: `zink/extractor.py:predict2` and its worker. Extend **`zink/tests/test_thread.py`** and **`test_thread2.py`** beyond their current punctuation checks.

- [ ] Pass each request's text directly to its workers instead of setting and deleting `self.thread_text`, or serialize the entire call if that is the appropriate supported contract.
- [ ] Audit adjacent shared state: replacement maps, cached entity dictionaries, lazy initialization, and the model's documented concurrent-call support. Keep the concurrency guarantee limited to what is tested.
- [ ] Build a deterministic overlapping-call reproduction with two distinct inputs and labels. Use events/barriers or a controllable executor; include timeouts and cleanup. Do not rely on sleeps or chance.
- [ ] Check both worker passes: first pass receives its own request, second pass masks only that request, and returned offsets/source text belong to the right input.
- [ ] Assert there is no `AttributeError`, mixed-request output, incorrect label set, or metadata leakage.
- [ ] Cover multiple label chunks, empty labels, worker failure followed by a successful call, and repeated sequential calls.
- [ ] Test concurrent top-level redaction/replacement with separate user mappings and cached/uncached paths; confirm one call cannot overwrite another's choices.
- [ ] Test parallel passage offsets and ordering when workers finish out of order. Keep existing punctuation checks as supplementary coverage.
- [ ] Run a bounded concurrent smoke test with the real model and record any backend limitations. Do not infer that concurrent persistent-file writes are safe from extractor-only tests.
- [ ] Update the tutorial's shared-extractor warning to reflect only the concurrency guarantees actually established; keep any remaining mapping-file/model limitations explicit.

Acceptance: the controlled regression reproduces the old race and reliably passes after the fix without deadlocking.

## T6 — Defer model initialization and measure import cost

Source: [reviewer 2, code comment 3](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6400697457).

Primary implementation: `zink/__init__.py`, `zink/extractor.py:_DEFAULT_EXTRACTOR`, `zink/pipeline.py`, `zink/passage_processors.py`, `zink/zink.py`. Extend **`tests/test_optional_backend.py`**.

- [ ] Measure cold subprocess `import zink` time and import profile before/after; distinguish backend imports, model loading, and replacement-data cache work.
- [ ] Introduce a shared lazy inference initializer and update all holders of `_DEFAULT_EXTRACTOR`; avoid stale references or accidentally creating multiple models.
- [ ] Keep missing-backend installation guidance actionable. If warning timing changes, document and test the intended contract; preserve the earlier import-warning request where practical without initializing a model.
- [ ] Ensure utility calls such as `prep()` and mapping-path helpers remain usable without an inference backend.
- [ ] Assert in subprocess tests that import and utility calls invoke neither `from_pretrained` nor model downloads/inference. Fail immediately if a forbidden initializer is called.
- [ ] Assert first inference initializes once and subsequent inference reuses the model; cover concurrent first use and a failed initialization followed by the documented retry/error behavior.
- [ ] Extend missing-GLiNER/missing-ONNX checks across `redact`, `replace`, and `replace_with_my_data`; confirm errors include CPU/GPU installation guidance.
- [ ] Confirm offline unit-test collection and Sphinx autodoc import no longer require model downloads.
- [ ] Update README, tutorial, contributing instructions, and Docker instructions if model setup moves from first import to first inference.

Acceptance: importing utilities triggers no model initialization; first-use inference still works. Report observed timings and environment; use semantic no-initialization assertions rather than a fragile universal millisecond test threshold.

## T7 — Complete public documentation with tested examples

Sources: both review checklists and [reviewer 2, code comment 2](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6400697457).

- [ ] Inventory exports in `zink.__all__`, documented classes, and server endpoints; map each public entry point to a docstring and runnable example.
- [ ] Fill class/method gaps in `Pseudonymizer`, `EntityExtractor`, and `zink/server.py`, using the established docstring style.
- [ ] Document actual behavior for consistency scope, protection boundaries, return metadata, numbered persistence, and model initialization.
- [ ] Keep unsupported custom-pipeline injection parameters clearly labeled. Either document their current unsupported status accurately or track an explicit separate implementation task.
- [ ] Cover `redact`, `replace`, and `replace_with_my_data` in **`test_basic.py`**; include the missing/empty custom-mapping error and custom placeholders.
- [ ] Cover `prep` in **`test_exclusion.py`** and mapping location/reset/idempotent reset in **`test_persistent_mapping.py`**.
- [ ] Extend **`test_shield.py`** for positional/keyword targets, missing target, non-string input, required labels, non-string output, exception propagation, and the unchanged wrapped-function metadata. Assert the wrapped function's actual input, not just restored output.
- [ ] Exercise the folder-of-text-files tutorial using a temporary directory and synthetic files; verify UTF-8/newlines, output naming, and stable numbering when enabled. Use a small additional test module only if no existing module fits this workflow.
- [ ] If changing or documenting the server, add endpoint smoke tests for health and successful redaction serialization. Explicitly install its optional test dependencies; do not make unrelated core tests depend on FastAPI.
- [ ] Build Sphinx with warnings treated as errors and inspect the generated API/tutorial pages for missing references and examples.

Acceptance: every claimed public feature has a working example and behavior-based test; docstrings and tutorial limitations match the tested API.

## T8 — Improve README discoverability, comparisons, and badges

Source: [reviewer 2, non-code comments and checklist](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6400697457).

- [ ] Keep the existing prominent documentation/tutorial/API links; verify the published pages resolve and show the reviewed release or clearly identified development version.
- [ ] Add a short README comparison with Presidio, scrubadub, PyRedactKit, and GLiNER, linking the existing detailed comparison and benchmark pages. Support claims with existing results and clearly state benchmark scope.
- [ ] Add supported-Python and docs-build badges reflecting the actual configured matrix/workflow.
- [ ] Add a coverage badge backed by measured CI coverage from T10; select a repository-supported reporting mechanism rather than a static invented percentage.
- [ ] Confirm existing CI/package-version badges still point to the right repository/workflows.
- [ ] In the review response, point out the existing documentation URL respectfully and identify what was improved so the reviewer can find it.

Acceptance: a README reader can find the API, tutorial, comparison, and real build/coverage status without searching the issue thread.

## T9 — Remove commented-out code and unused experimental files

Source: [reviewer 2, code comments 1 and 4](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6400697457).

- [ ] Remove the obsolete commented `predict_thorough` and `redact` implementations and stale implementation-discussion comments; retain useful behavioral explanations.
- [ ] Audit `zink/misc` (the directory is inside the package), including imports, documentation, data files, and packaging references.
- [ ] Remove unused experimental scripts if the audit confirms they are unreferenced. If a script is useful, move it to an appropriate developer location and document its dependencies and inputs.
- [ ] Expand Ruff's current undefined-name-only configuration to a deliberate, manageable formatting/linting standard; fix the selected violations and enforce it in CI.
- [ ] Run the full feature suite, strict docs build, and installed-wheel smoke tests after cleanup. Inspect the wheel/sdist to confirm required subpackages and bundled replacement data remain present.

Acceptance: no obsolete implementations remain in comments; retained scripts have a purpose; cleanup does not alter tested feature behavior or packaged resources.

## T10 — Validate Python support, coverage, builds, and Docker

Source: [reviewer 2, code comment 5 and packaging checklist](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6400697457).

- [ ] Check Python release support and actual dependency-wheel availability at implementation time. Do not equate the end of active bug-fix support with end of security support.
- [ ] Add newer supported Python versions to `.github/workflows/python-tests.yaml` after verifying GLiNER/ONNX compatibility on each target OS. Retain the declared minimum where supported; document any deliberate support-policy change.
- [ ] Keep the three existing OS targets. Run deterministic tests on all supported combinations and explicit real-CPU integration jobs on the combinations claimed as supported; document any reduced integration matrix and reason.
- [ ] Make model setup reproducible: record/pin the revision used for verification, use a revision-aware cache key, and audit the current dummy `pytorch_model.bin` workaround before carrying it forward.
- [ ] Add `pytest-cov` to development/test tooling; collect branch coverage for application code, publish reports, inspect uncovered changed branches, and establish a measured baseline for future regression gating.
- [ ] Preserve `tests/test_benchmark_scoring.py` and `tests/test_qib_metrics.py` in CI; avoid rerunning the expensive full Presidio benchmark unless a relevant detection/scoring claim changes.
- [ ] Build wheel and sdist; install each in a clean environment outside the checkout and run import, bundled-data, optional-backend, and representative feature smoke tests. Checkout `pythonpath` must not mask a missing packaged module.
- [ ] Update Docker to a newer Python base proven compatible by these checks. Reconcile Python references in contributing instructions, docs workflows, and Read the Docs configuration as needed.
- [ ] Build/run the image; check `/health`, a representative `/redact` request, response serialization, and a subsequent request. Verify cached inference works without network after model preload.
- [ ] Run the corrected examples and real-model feature suite before release; report exact failures/skips instead of broadly declaring GPU or untested platforms supported.

Commands to record once the relevant tooling/markers are implemented:

```bash
python -m pytest tests zink/tests -m 'not integration' -q
python -m pytest tests zink/tests -m integration -q
python -m pytest tests zink/tests --cov=zink --cov-branch --cov-report=term-missing --cov-report=xml
python -m ruff check .
python -m sphinx -b html -W --keep-going docs/source docs/build/html
python -m build
```

The marker commands depend on T1/T6. Coverage and build commands require adding their development tools; they are not all runnable in the current environment.

Acceptance: the declared Python/OS matrix passes; the real backend is exercised; coverage reports show the new branches tested; distributable artifacts and the container work independently of the source tree.

## T11 — Reconcile release tags and prepare review artifacts

Source: [editor's release request](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6180673442).

- [ ] Inspect remote tags/releases and version history before creating anything; confirm whether the editor's reported missing releases remain missing.
- [ ] Identify the exact historical commits for `0.6.4`, `0.6.5`, and `0.7.0`, checking package metadata/artifacts where available. Record uncertainty rather than guess a release commit.
- [ ] Prepare tags/releases for the genuine historical snapshots. Preserve `v0.7.0` as the submitted version; do not point a historical tag at newly fixed code.
- [ ] Choose a new patch version for the fixes, update all version sources and release notes, and identify that version explicitly for re-review.
- [ ] Complete artifact checks against the final candidate commit and prepare GitHub release notes, wheel/sdist, and a clear reviewer install command.
- [ ] Prepare the archive/DOI steps for acceptance in line with the editor's instructions; distinguish the submitted snapshot from the later accepted version.

Acceptance: historical release identity is accurate and the fixes have an unambiguous, tested release candidate. Tag/release publication is a later action, not performed by creating this task list.

## T12 — Completion evidence and point-by-point review response

- [ ] For each reviewer/editor comment, record the implementation commit, affected files, regression test names, and result. Explain any suggestion intentionally deferred.
- [ ] For each correctness bug, demonstrate a meaningful test failing before the fix and passing afterward; retain the test permanently in the existing suite.
- [ ] Record full-suite counts, expected skips, Python/OS/backend/model versions, strict docs/lint/build results, coverage, and Docker checks.
- [ ] Recheck the earlier dependency warning, approximate download-size warning, advanced file tutorial, and Presidio benchmark links after import/packaging changes.
- [ ] Update `pyopensci-response.md` with a review-ready response and links to the candidate release, existing documentation, and verification evidence.
- [ ] Request re-review only after required fixes and verification are complete. Posting the response is a separate publication action.

Definition of done: every required comment has a tested fix or a documented explanation; the existing feature tests are expanded rather than bypassed; real-model and deterministic checks both pass; the release and response identify exactly what was verified.
