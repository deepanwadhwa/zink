# Zink 0.7.1 review validation

The review fixes were merged through [PR #16](https://github.com/deepanwadhwa/zink/pull/16).
Version 0.7.1 is published at release commit
`5503065c09db1948b27af5cddb5cf6632b3839ba`. Core source/test fixes run through
`93a5c38648b5f4e7eea74b87cc5f97a3319ee3ca`; subsequent commits add publishing
configuration and verification records. See `RELEASE_EXECUTION.md` for the
published artifacts, hashes, live documentation, and posted re-review request.

## Results

| Check | Environment and result |
| --- | --- |
| Original full-suite baseline | 41 passed in 59.71 seconds, clean archive of the reviewed commit, macOS arm64 / Python 3.13.13 |
| Final full suite with coverage | 186 passed in 84.20 seconds, macOS arm64 / Python 3.13.13 / GLiNER 0.2.29 / ONNX Runtime 1.30.0 |
| Final full Linux suite | 186 passed in 80.86 seconds, Linux arm64 / Python 3.13 / GLiNER 0.2.30 / ONNX Runtime 1.32.0 |
| Deterministic base-package suite | 152 passed on each of Python 3.11.15, 3.12.8, and 3.14.7; 34 model-backed tests explicitly deselected |
| Branch-enabled coverage | 92.17% combined statement/branch coverage; the configured 90% gate passes |
| Core transformations | Replacer, merger, date strategy, person strategy, bundled mapping, public API, and result objects report 100% in this run |
| Strict documentation | Sphinx HTML build with `-W --keep-going` passes; generated API and tutorial pages inspected |
| Style and lockfile | Ruff lint, Ruff formatting, diff whitespace, and `uv lock --check` pass |
| Workflow definitions | Six workflow definitions parse; referenced action tags resolve; the publishing workflow successfully ran through OIDC upload |
| Wheel and source archive | Both build with isolated Hatchling; both install and pass the distribution smoke helper from outside the checkout |
| Installed wheel CPU inference | Real model runs offline from an isolated wheel installation; import resolves to that environment's site-packages |
| Docker | Python 3.13 image builds and verifies installed-package inference offline with the complete pinned snapshot |

The model revision is `40349bb15d985ced384bed5c35115fd70069f4b9` throughout.
The full suite contains 152 deterministic checks and 34 CPU-model checks.
On Windows, the POSIX-specific Tokyo timezone subprocess check is explicitly
skipped because `time.tzset` is unavailable.

The complete [GitHub-hosted Python 3.11–3.14 / Linux, macOS, and Windows matrix](https://github.com/deepanwadhwa/zink/actions/runs/44547593795)
passed. All 28 hosted checks passed, including documentation, style, coverage,
and independent distribution installation. The workflows published coverage
and distribution artifacts. GPU behavior is not claimed as verified by this
CPU matrix. [PyPI Trusted Publishing](https://github.com/deepanwadhwa/zink/actions/runs/44549755942)
also succeeded, and the uploaded hashes match the verified GitHub release assets.

## Regression evidence

| Problem | Failing behavior confirmed before the fix | Permanent coverage and change |
| --- | --- | --- |
| Consistent replacement used global string replacement | `Aliceette`; undetected occurrences changed | Existing `test_basic.py`, span replacement and defensive cached metadata; `71dd634` |
| Overlapping protected phrases corrupted markers | `**Alice* arrived*.` became `person_REDACTED arrived.` | Existing `test_exclusion.py`; `4faeae6` |
| Shared extractor request text | Cross-request masking and missing `thread_text` attribute | Existing thread tests with bounded events and real CPU checks; `bbdf673`, `359e2cf` |
| Shared replacement mapping | Overlapping requests produced `Alice met David.` | Existing basic/thread tests with independent user mappings; `71dd634`, `359e2cf` |
| Published examples did not match the API | Wrong keyword and tuple replacement errors | Actual README/RST code blocks execute in tests; `4faeae6` |
| Nested/crossing detections broke span rendering | Duplicated replacement output and unreplaced detected characters | Merger union/priority, order, validation, and no-mutation cases in `test_pipeline_contracts.py`; `71dd634` |
| Merging before protection hid a separate detection | Protecting Alice also left independently detected Jones intact | Raw extraction cache, protection before merging, and region boundaries; four regressions failed before `1270450` |
| Protected gaps were merged back into a replacement | `Ann*x*Bob` suppressed the outside detections | Existing exclusion regression, preserved protected regions; `1270450` |
| Date and name replacement edge cases | Weekday became numeric date, bounds ignored, padded day reused, source name token retained | Existing basic tests with controlled providers; `8c67319` |
| Timezone conversion moved a bounded date | Tokyo one-day 1900-01-01 range returned 1899-12-31 | Calendar-day generation, ambiguous date exclusion, invalid range and POSIX subprocess regressions; `b58b1c0` |

The original real-model exclusion test assumed that protecting Toyota also
suppressed the independently detected word “car.” Its expectation now requires
Toyota to survive while the unprotected detection is redacted (`93a5c38`).
The same correction is enforced by deterministic overlapping-span regressions.

## Test isolation and limits

Each test gets temporary numbered mappings, a fresh public pipeline, and
cleared extraction/replacement caches. Deterministic checks supply model
responses through scoped fixtures; integration tests keep the real backend.
Model loading tests run in fresh subprocesses and prohibit heavy imports or
initialization during utility use. Concurrent tests use events/barriers and
timeouts, not sleeps or timing luck.

First-use model initialization is serialized; subsequent calls keep text,
labels, masks, replacement maps, and result metadata private to the request.
Numbered mapping updates are serialized across threads in one process.
Multiple processes modifying the same mapping file still need coordination.
Fixed-width chunking can split entities; the tutorial retains the relevant
long-document limitation.

Coverage includes application branches, not the test modules. Remaining
uncovered paths include legacy unused helper classes, development gzip
utilities, and some backend/error fallbacks. They are included in the reported
total rather than excluded to inflate it. The run emits two upstream
Torch/Hugging Face deprecation warnings; neither is a failing check.

## Reproduce

```sh
python -m pip install -e '.[cpu,server,test]'
python scripts/prepare_model.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest --strict-markers --cov=zink --cov-branch --cov-report=term-missing --cov-report=xml
python -m ruff check .
python -m ruff format --check zink tests scripts conftest.py
python -m sphinx -b html -W --keep-going docs/source build/validation/docs
python -m build
```

Use `python -m pytest -m 'not integration' --strict-markers` for the base-package
checks. The development environment additionally needs Ruff, Sphinx and the
theme, and `build`; these are listed in the development dependency group.
`scripts/verify_distribution.py --version 0.7.1` is run with each installed
environment's Python using `-I`, from a temporary directory outside the checkout.
Add `--cpu` when that environment has the real backend and prepared model.

The final local archives are in `dist/`. Their SHA-256 values are written to
`dist/SHA256SUMS` after building, avoiding a self-referential checksum inside
the source archive. Package contents are checked for all required subpackages
and bundled gzip data; the wheel omits tests, and neither archive contains
the removed experiments or generated ONNX session files.

## Acceptance follow-up

The hosted matrix, historical release backfill, 0.7.1 GitHub/PyPI publication,
live documentation verification, and [re-review request](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-7012929949)
are complete. Reviewers still need to approve the package. At acceptance,
verify the editor-approved version's archive DOI. The old README DOI refers
to version 0.2.1 and must not be presented as the accepted 0.7.1 archive.
