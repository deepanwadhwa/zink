# Zink release preparation

The three missing historical tags have exact matches in the published PyPI
source archives. Version `0.7.1` is the candidate for re-review of
[pyOpenSci submission #352](https://github.com/pyOpenSci/software-submission/issues/352).

## Historical tags

GitHub listed `v0.5.1`, `v0.6.0`, `v0.6.1`, and `v0.6.3`
when checked. The versions below already have PyPI releases and can be
backfilled on GitHub. [GitHub releases](https://github.com/deepanwadhwa/zink/releases)

| Tag | Verified Git commit | Published PyPI source archive | Matched tracked files |
| --- | --- | --- | ---: |
| `v0.6.4` | [`2c2617c585e1387f6944fb4949c0e3e7371b8c96`](https://github.com/deepanwadhwa/zink/commit/2c2617c585e1387f6944fb4949c0e3e7371b8c96) | [Zink 0.6.4](https://pypi.org/project/zink/0.6.4/#files) | 123 |
| `v0.6.5` | [`690535680410e4de022356509706781dd0afe4ff`](https://github.com/deepanwadhwa/zink/commit/690535680410e4de022356509706781dd0afe4ff) | [Zink 0.6.5](https://pypi.org/project/zink/0.6.5/#files) | 124 |
| `v0.7.0` | [`0beab1d1ceb6a0fd741088339dfd5b58560a0216`](https://github.com/deepanwadhwa/zink/commit/0beab1d1ceb6a0fd741088339dfd5b58560a0216) | [Zink 0.7.0](https://pypi.org/project/zink/0.7.0/#files) | 126 |

Each downloaded `.tar.gz` matched the SHA-256 recorded by PyPI. Its
regular file paths and contents then matched the full tracked Git tree
for the indicated commit, including README, package configuration, code,
tests, and data. The archive's generated `PKG-INFO` was the sole extra file.
Each tree was the only exact match among candidate commits carrying that
version in the repository's release history.

```text
a6231f9b21e0326618b53a9718f4cc0c23ad2b4a8338bd6327105c12b9242c4e  zink-0.6.4.tar.gz
1292ba1fd0df8016293fc564dfa446dde17894cf0e88ab6f5d0e30942e3a773e  zink-0.6.5.tar.gz
e4d361b4955d3219a3f90d7f5263c6f1c1aa08ac5807258b1b0549f79901f337  zink-0.7.0.tar.gz
```

The first reviewer used [`4f7c41837ced05d5ef2638be07b4c95c0a62a380`](https://github.com/deepanwadhwa/zink/commit/4f7c41837ced05d5ef2638be07b4c95c0a62a380),
a later snapshot that still reported `0.7.0`. It differs from the PyPI
archive in 11 shared files and contains 42 additional tracked files. Use the
published source match for `v0.7.0` and identify the review snapshot by its
commit when replying to the editor. [Editor's release request](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6180673442)
· [First review](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-6209920390)

### Historical release notes

- **Zink 0.6.4** adds a configurable file for persistent numbered entity
  mappings. This GitHub entry records the source of the existing
  [PyPI release](https://pypi.org/project/zink/0.6.4/).
- **Zink 0.6.5** uses a default numbered entity mapping file and adds helpers
  to locate or reset it. This GitHub entry records the source of the existing
  [PyPI release](https://pypi.org/project/zink/0.6.5/).
- **Zink 0.7.0** adds protected spans for redaction and `prep()` to mark
  exclusions. This GitHub entry records the source of the existing
  [PyPI release](https://pypi.org/project/zink/0.7.0/).

Recheck the remote refs before creating the annotated tags and publish
historical GitHub releases without setting them as the latest release.
Link each release to the existing PyPI files.

## Version 0.7.1 candidate

Use the final tested review commit for the candidate and record its complete
SHA alongside the test results. Build a wheel and source distribution from
that commit, verify both report version `0.7.1`, and test both installs
from outside the source checkout. Attach or link the verified artifacts and
their SHA-256 hashes in the release. Use the pinned commit as the review
reference until a release is available.

### Draft release notes

- Apply consistent replacements only to detected spans, and merge overlapping
  protection markers while preserving original text.
- Isolate input and replacement state between concurrent calls. Initialize the
  inference backend on first use and keep numbered mappings consistent within
  a process.
- Correct the README examples and expand the API, tutorial, and server
  documentation. Add regression tests and report branch coverage.

Once the tag is available, a reviewer can install its CPU build in a clean
environment and run the quick start:

```sh
python -m pip install "zink[cpu] @ git+https://github.com/deepanwadhwa/zink.git@v0.7.1"
python -c 'import zink; print(zink.redact("Alice is here.", categories=("person",)).anonymized_text)'
```

## Archive when pyOpenSci accepts the package

1. Record the editor-approved version, full commit, and approval date.
   A tag for the reviewed fixes can serve as the accepted source if the
   editor approves that exact version. [pyOpenSci author guide](https://www.pyopensci.org/software-peer-review/how-to/author-guide.html#my-package-is-approved-now-what)
2. Verify whether the repository's Zenodo integration already archived the
   approved GitHub release. If a manual archive is needed, create a new
   version of the existing software record, with source from the approved
   GitHub tag and the correct version, creator, and license metadata.
   [GitHub release archive](https://help.zenodo.org/docs/github/archive-software/github-upload/)
   · [Zenodo versioning](https://help.zenodo.org/docs/deposit/manage-versions/)
3. Resolve the new version-specific DOI and verify its metadata and files
   against the approved tag. The current README DOI identifies the older
   `v0.2.1` archive. [Existing DOI record](https://zenodo.org/records/15035072)
4. Give the editor the accepted release URL, verified archive DOI, and
   version for the issue. Add the pyOpenSci badge after approval and update
   the project citation with the accepted version's DOI.
   [pyOpenSci approval process](https://www.pyopensci.org/software-peer-review/how-to/review-process.html)
