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
- Replacement consistency keeps v0.7.1's exact-source-text default across
  labels. v0.7.2 adds the keyword-only `consistency_scope="label"` option, so
  users can explicitly choose `(normalized label, exact source text)` reuse
  within a call. A person named Jordan and a location named Jordan can then
  independently respect their category’s replacement. Existing positional
  arguments and the default three-argument custom-replacer protocol are retained.
- Mapping updates use an atomic replacement from a private temporary file.
  POSIX files use `0600`, including updates to previously permissive files;
  newly created mapping directories use `0700`. Failed serialization or file
  replacement preserves the old mapping and removes the temporary file.

## Validation

- Full local suite: **419 passed**, including **46 real-model tests**, with
  **93.25% combined statement/branch coverage**, above the 90% requirement.
- Model-free suite: **373 passed** on each of Python 3.11, 3.12, 3.13, and 3.14.
- Ruff passes, and Sphinx builds with warnings treated as errors.
- The 0.7.2 wheel and source archive each install and pass the distribution
  smoke checks in separate clean environments outside the checkout.
- The suite adds 233 cases to the 186-case baseline, including controlled
  multiword, dotted, hyphenated, Unicode, and dash-containing names; original
  offsets; overlap deduplication; out-of-order workers; protected text; ID
  capacity and error recovery; and POSIX creation/update permissions.
- Compatibility checks run against an isolated PyPI v0.7.1 installation confirm
  the same omitted/default/disabled consistency outputs in both public APIs.
  v0.7.1 rejects the new keyword with `TypeError`; v0.7.2 accepts both scopes.
  Regression tests cover old positional arguments, legacy custom replacers,
  opt-in custom replacers, candidate lists, invalid scopes before inference,
  copied README code, alternating scopes, and concurrent requests.
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

`ensure_consistency=True` retains v0.7.1's first-source-string-wins behavior
across labels. `consistency_scope="text"` is the default in v0.7.2; explicitly
choose `consistency_scope="label"` for label-specific reuse. v0.7.1 and older
versions do not accept the new keyword and raise `TypeError` if it is supplied.
With `ensure_consistency=False`, all mentions choose independently and scope
has no effect. Invalid scope values raise `ValueError` before inference even
when consistency is disabled. The README and API reference contain a version
and output table, and the tutorial explains the migration.

Replacement rules remain category based; the extractor determines each label.
Label matching is case insensitive and source matching is case sensitive.
Consistency does not perform real-world identity resolution. Custom replacers
opting into label scope must accept the new keyword in their consistent method.

POSIX permission bits do not specify Windows ACL behavior. Windows access must
be restricted through the directory’s access controls. Atomic writes protect
file integrity but do not coordinate updates from multiple processes; keep
numbered mapping writes in one process, as documented.
