# Reviewer edge-case fixes for 0.7.2

The four observations on reviewed release 0.7.1 were reproduced locally,
including real ONNX inference at both 16- and 1,000-character boundaries.

## Changes

- Chunking finishes whitespace-delimited words and adds 32–128 characters of
  context on each side, extended to complete words. This preserves punctuation
  inside names and provides context for entities crossing a core boundary.
  Identical inference windows are processed once. Duplicate spans retain their
  highest score, and detections must intersect the owning core. The reviewer’s
  `Alice Smith` example is covered by real-model tests across all three APIs.
- Numbered-ID allocation samples from the remaining IDs without retrying
  collisions. A new source string raises `ValueError` when its label’s 9,000
  four-digit IDs are occupied. Existing IDs remain reusable. Exhaustion leaves
  the persistent mapping unchanged, including when a request first allocates
  the last free ID and then needs another.
- Replacement consistency uses `(normalized label, exact source text)` per
  call. A person named Jordan and a location named Jordan now independently
  respect their category’s replacement. Candidate lists still reuse the choice
  for repeated mentions within the same label.
- Mapping updates use an atomic replacement from a private temporary file.
  POSIX files use `0600`, including updates to previously permissive files;
  newly created mapping directories use `0700`. Failed serialization or file
  replacement preserves the old mapping and removes the temporary file.

## Validation

- Full local suite: **337 passed**, including **46 real-model tests**, with
  **93.16% combined statement/branch coverage**, above the 90% requirement.
- Model-free suite: **291 passed** on each of Python 3.11, 3.12, 3.13, and 3.14.
- Ruff passes, and Sphinx builds with warnings treated as errors.
- The 0.7.2 wheel and source archive each install and pass the distribution
  smoke checks in separate clean environments outside the checkout.
- The suite adds 151 cases to the 186-case baseline, including controlled
  multiword, dotted, hyphenated, Unicode, and dash-containing names; original
  offsets; overlap deduplication; out-of-order workers; protected text; ID
  capacity and error recovery; and POSIX creation/update permissions.
- Normal hosted CI is required on the final commit, including the complete
  Linux/macOS/Windows and Python 3.11–3.14 unit/integration matrix, coverage,
  documentation, lint, and independent wheel/source-distribution checks.

## Behavior and limits

`chunk_size` is now a soft character target. Context windows can be longer,
and extremely long whitespace-free text can exceed backend input limits.
Finite overlap improves boundary recognition but cannot guarantee perfect
model recall or complete detection of entities longer than the context.

The 9,000-ID limit applies per label to persisted distinct source strings
across calls and sessions. Detection and ordinary redaction have no such limit.
Deleting mappings discards the ability to reuse or restore those IDs, so it
should be a deliberate operation.

Cross-label consistency changes from 0.7.1’s first-source-string-wins behavior.
Replacement rules remain category based; the extractor determines the label of
each mention. Label matching is case insensitive and source matching is case
sensitive. Consistency does not perform real-world identity resolution.

POSIX permission bits do not specify Windows ACL behavior. Windows access must
be restricted through the directory’s access controls. Atomic writes protect
file integrity but do not coordinate updates from multiple processes; keep
numbered mapping writes in one process, as documented.
