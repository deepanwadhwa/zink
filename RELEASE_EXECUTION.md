# Zink 0.7.1 release execution

Goal: finish hosted validation, publish the verified historical releases and
0.7.1 update, verify published documentation, and request pyOpenSci re-review.
Acceptance-dependent archive/DOI work is prepared separately and follows
reviewer approval.

- [x] Push `fix/pyopensci-review-352` and open [PR #16](https://github.com/deepanwadhwa/zink/pull/16).
- [x] Publish [v0.6.4](https://github.com/deepanwadhwa/zink/releases/tag/v0.6.4), [v0.6.5](https://github.com/deepanwadhwa/zink/releases/tag/v0.6.5), and [v0.7.0](https://github.com/deepanwadhwa/zink/releases/tag/v0.7.0) against the verified original PyPI source commits. Each includes its original source archive; none replaces the latest release.
- [x] Pass hosted [lint](https://github.com/deepanwadhwa/zink/actions/runs/44547593457), [documentation](https://github.com/deepanwadhwa/zink/actions/runs/44547593545), [distribution](https://github.com/deepanwadhwa/zink/actions/runs/44547593433), and [coverage](https://github.com/deepanwadhwa/zink/actions/runs/44547593629) checks. Hosted combined statement/branch coverage is 92.17%.
- [x] Complete the [24-job unit/CPU matrix](https://github.com/deepanwadhwa/zink/actions/runs/44547593795). All 28 hosted test/build/documentation checks passed across Python 3.11–3.14 on Linux, macOS, and Windows.
- [x] Merge the verified release branch through [PR #16](https://github.com/deepanwadhwa/zink/pull/16), preserving the focused commits. Merge/release commit: `5503065c09db1948b27af5cddb5cf6632b3839ba`, whose file tree matches the tested PR head.
- [x] Tag and publish [v0.7.1 on GitHub](https://github.com/deepanwadhwa/zink/releases/tag/v0.7.1) with the verified hosted wheel, source archive, and `SHA256SUMS`.
- [x] Publish [Zink 0.7.1 to PyPI](https://pypi.org/project/zink/0.7.1/) through [Trusted Publishing](https://github.com/deepanwadhwa/zink/actions/runs/44549755942). Both uploaded hashes match the verified GitHub assets. A fresh PyPI installation passed package, replacement-data, transformation, and HTTP smoke checks outside the checkout.
- [x] Verify [Read the Docs latest](https://zink.readthedocs.io/en/latest/) and [stable](https://zink.readthedocs.io/en/stable/), API, and tutorial pages return HTTP 200 and identify version 0.7.1. Latest build `36016392` and stable build `36016411` succeeded from the release commit.
- [x] Post the [point-by-point response and re-review request](https://github.com/pyOpenSci/software-submission/issues/352#issuecomment-7012929949), including the updated AI-assistance disclosure and links to release/CI evidence.

## Published artifact hashes

These match the hosted distribution build, GitHub release, and PyPI JSON metadata:

```text
ca0cb1d44af4213edd12709984e39c683d3eb37329e7bcbb1b4342f83b3cf284  zink-0.7.1-py3-none-any.whl
5a43bd9c069fa2bbb2d5485370df12bc9e7999930955ebcb50f0eb39d3fa59cd  zink-0.7.1.tar.gz
```

Maintainer release/submission actions are complete. The review remains open
for reviewer approval. After acceptance, verify the editor-approved version
and create/verify its version-specific archive DOI as described in
`RELEASE_PREPARATION.md`; the older 0.2.1 DOI is not the 0.7.1 archive.

## PyPI publishing identity

The prepared GitHub workflow supports existing Trusted Publishing or a
project-scoped repository secret named `PYPI_API_TOKEN`. No API token was
found in the usual local configuration or repository secrets. The maintainer
confirmed adding the Trusted Publisher below on PyPI, and the corresponding
GitHub environment is configured. The successful publish run verified the OIDC
exchange without an API token.

The current Trusted Publisher identity is:

- Owner: `deepanwadhwa`
- Repository: `zink`
- Workflow filename: `publish.yaml`
- GitHub environment: `pypi`

If the existing PyPI publisher uses a different workflow/environment, match
the workflow to that identity rather than creating another token unnecessarily.
