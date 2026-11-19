# Draft response for pyOpenSci submission #352

Prepared locally for posting after the branch is pushed and hosted checks pass.
Version `0.7.1` is the proposed update. No review reply or release has been published.

Hi @yeelauren, @korsakowii, and @erik-whiting — thank you for the reviews.
The changes below address the submitted source snapshot and add regression
coverage to the existing feature tests.

## Reviewer 1

1. **Consistent replacements:** replacements now use detected offsets in the
   original text. The `Ann`/`Annette` reproduction produces
   `Alice met Alice; Alice arrived later.` Tests also cover undetected
   occurrences, inserted values containing source names, candidate lists,
   independent replacement, cache isolation, and concurrent requests.
2. **Overlapping protection:** `prep()` collects and merges matching spans
   before inserting markers, retaining original casing. Protection is applied
   to raw detections before merging. Independently detected names outside a
   protected phrase remain eligible for redaction, and merging cannot bridge
   across protected text. Tests cover nested and crossing phrases, repeated
   matches, Unicode, cache reuse, chunk boundaries, and numbered mappings.
3. **README examples:** the numbering examples use `categories=`, and custom
   replacement candidates use a list. Tests execute the actual README blocks
   and folder-processing tutorial, including real CPU-model example checks.
4. **Concurrent extraction:** request text and masks are now local to each
   call. Model initialization is shared and lazy. Event-controlled regressions
   cover overlapping requests, masking passes, independent replacement maps,
   worker failures, and out-of-order passage completion. CPU-model concurrent
   inference is also tested. Numbered mapping updates are serialized within
   one process; separate processes still require external coordination.

The default merger also resolves crossing and nested detections into
non-overlapping spans covering their union, preventing span-based replacement
from duplicating or leaving behind part of a detected entity.

## Reviewer 2

1. **Documentation, examples, and README:** the documentation site already
   existed at <https://zink.readthedocs.io/en/latest/>. The README links directly
   to the tutorial and API reference. The update expands runnable examples,
   adds a short comparison with related tools, and adds supported-Python,
   docs-build, and coverage-workflow badges. Coverage reports are generated
   from the test run rather than represented by a static percentage.
2. **Commented-out code:** the obsolete extractor and pipeline implementations
   have been removed. Ruff linting and formatting checks are enforced in CI.
3. **Docstrings:** the pipeline and extractor now have class documentation;
   public methods, result fields, optional components, and HTTP endpoints are
   documented with their behavior and limitations.
4. **Import performance:** importing Zink no longer loads the inference model,
   imports the heavy backend, or creates a replacement-data cache. Missing
   inference packages still produce installation guidance. A fresh offline
   import with the model already cached took approximately 0.12 seconds,
   compared with 9.23 seconds before the change on the same machine. These
   are single observations; subprocess tests enforce the no-initialization
   behavior independently of timing.
5. **Experimental directory:** the unreferenced `zink/misc` scripts and duplicate
   unused cache helpers have been removed. Installed-distribution checks
   verify that required subpackages and replacement data remain present.
6. **Python and Docker:** the Docker base is Python 3.13. Unit and CPU-model
   workflows cover Python 3.11–3.14 across Linux, macOS, and Windows. Local
   verification and the distinction from the pending hosted matrix are
   recorded in the validation report. The container preloads the pinned
   published model snapshot and verifies offline inference without writing
   an artificial model placeholder.

Broader replacement tests also found and fixed weekday/date-range handling,
timezone-sensitive date generation, and generated names retaining a source
token. These have deterministic regression tests in the existing basic suite.

## Release identity and verification

The missing historical GitHub releases are prepared for the exact commits
matching the published PyPI source archives:

- `0.6.4`: `2c2617c585e1387f6944fb4949c0e3e7371b8c96`
- `0.6.5`: `690535680410e4de022356509706781dd0afe4ff`
- `0.7.0`: `0beab1d1ceb6a0fd741088339dfd5b58560a0216`

The reviewed `4f7c41837ced05d5ef2638be07b4c95c0a62a380` snapshot is later than
the PyPI `0.7.0` archive and remains identified by its commit. The fixes are
prepared as `0.7.1`; historical release tags will not be moved to the new code.

See `REVIEW_VALIDATION.md` for test counts, coverage, environments, and
regression evidence, and `RELEASE_PREPARATION.md` for historical archive
checksums and publication steps. Before posting, replace these filenames with
links to the pushed files and attach the successful hosted-check and release
URLs. The final accepted version will need its own verified archive DOI.
