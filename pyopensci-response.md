# Posted pyOpenSci response

Posted at https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-7012929949 on 2026-11-19.

Hi @yeelauren, @korsakowii, and @erik-whiting — Zink **0.7.1** is now available on [PyPI](https://pypi.org/project/zink/0.7.1/) and [GitHub](https://github.com/deepanwadhwa/zink/releases/tag/v0.7.1). The [updated documentation](https://zink.readthedocs.io/en/latest/) is live. Please re-review this version.

The changes are in [PR #16](https://github.com/deepanwadhwa/zink/pull/16), merged at `5503065c09db1948b27af5cddb5cf6632b3839ba`.

### Reviewer 1

1. **Consistent replacements:** replacement values are applied only to detected offsets in the original text. The `Ann`/`Annette` example now produces `Alice met Alice; Alice arrived later.` Added regressions for undetected occurrences, inserted values containing another source name, both consistency modes, candidate lists, cache isolation, and concurrent replacement mappings.
2. **Overlapping protection:** `prep()` collects and merges spans before inserting markers, preserving source casing. Raw predictions are filtered against protection before merging, so an overlapping protected prediction cannot hide a separately detected entity outside it. Merging also cannot bridge a protected gap. Tests cover nested/crossing phrases, repeated matches, Unicode, cache reuse, chunk boundaries, and numbered mappings.
3. **README examples:** numbering calls use `categories=`, and replacement candidates use a list. Tests execute the actual README code blocks and folder-processing tutorial, including real CPU-model checks for the main examples.
4. **Concurrent extraction:** request text and masks are local to each call, and model initialization is shared and lazy. Event-controlled regressions cover overlapping requests, independent masking/replacement maps, worker failure recovery, and out-of-order passage completion. Real CPU-model concurrency checks also pass. Numbered mapping updates are serialized across threads in one process; separate processes still require coordination.

The default merger also handles nested/crossing predictions using non-overlapping spans covering their union, preventing span rendering from duplicating or leaving behind detected text.

### Reviewer 2

1. **Documentation and README:** the documentation site already existed, and its [API](https://zink.readthedocs.io/en/latest/api.html), [tutorial](https://zink.readthedocs.io/en/latest/tutorial.html), and [related-tools comparison](https://zink.readthedocs.io/en/latest/related-tools.html) are linked prominently. Examples and docstrings now cover the public interface, pipeline/extractor classes, result fields, and optional HTTP server. The README includes supported-Python, docs-build, and coverage-workflow badges, plus a short comparison with related packages. Measured coverage reports are attached to CI runs.
2. **Commented-out code:** obsolete extractor and pipeline implementations have been removed. Ruff linting and formatting are enforced in CI.
3. **Import performance:** importing Zink no longer initializes the model, imports the heavy backend, or creates a replacement-data disk cache. Missing inference dependencies still produce installation guidance. Fresh offline import with an already-cached model measured about 0.12 seconds versus 9.23 seconds before the change on the same machine. These are single measurements; subprocess tests separately enforce the no-initialization contract.
4. **Experimental directory:** unreferenced `zink/misc` scripts and duplicate unused cache helpers have been removed. Distribution checks verify required modules and bundled replacement data remain present.
5. **Python and Docker:** Docker uses Python 3.13. Hosted unit and real-CPU integration checks passed on Python 3.11–3.14 across Linux, macOS, and Windows. The container preloads the complete pinned published model snapshot and passes offline health/redaction checks without manufacturing a model placeholder.

Broader replacement tests also found and fixed weekday/date-range handling, timezone-sensitive bounded dates, and generated names retaining an original name token. These regressions are included in the existing basic test suite.

### Verification and releases

- **28 hosted checks passed**, including the [complete unit/CPU matrix](https://github.com/deepanwadhwa/zink/actions/runs/44547593795), [coverage](https://github.com/deepanwadhwa/zink/actions/runs/44547593629), [documentation](https://github.com/deepanwadhwa/zink/actions/runs/44547593545), [lint](https://github.com/deepanwadhwa/zink/actions/runs/44547593457), and [independent distribution installs](https://github.com/deepanwadhwa/zink/actions/runs/44547593433).
- The full suite passed **186 tests** locally on both macOS and Linux. Hosted combined statement/branch coverage is **92.17%**. A POSIX-only timezone subprocess test is explicitly skipped on Windows.
- [Trusted Publishing to PyPI](https://github.com/deepanwadhwa/zink/actions/runs/44549755942) succeeded. Published wheel/source hashes match the verified GitHub release assets, and a clean PyPI install passed the distribution smoke checks outside the checkout.
- The missing historical [v0.6.4](https://github.com/deepanwadhwa/zink/releases/tag/v0.6.4), [v0.6.5](https://github.com/deepanwadhwa/zink/releases/tag/v0.6.5), and [v0.7.0](https://github.com/deepanwadhwa/zink/releases/tag/v0.7.0) GitHub releases are published against commits matching their complete original PyPI source archives. The original reviewed `4f7c41837ced05d5ef2638be07b4c95c0a62a380` snapshot is identified separately; historical tags were not moved to the new fixes.

For re-review:

```sh
python -m pip install "zink[cpu]==0.7.1"
```

The first inference downloads approximately 2 GB of model files. GPU behavior is not claimed as verified by this CPU matrix. The accepted version's archive DOI will be verified after approval; the old README DOI refers to the earlier 0.2.1 archive.

**Development disclosure:** OpenAI Codex was used in November 2026 to implement and revise these fixes, regression tests, documentation, and CI/release configuration, including span replacement, protected-text handling, and request isolation. The linked local and hosted verification covers the resulting package.
