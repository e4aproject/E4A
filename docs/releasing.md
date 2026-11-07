# Releasing E4A

Releases are **manual and maintainer-approved**. No automation publishes
to PyPI or npm: the previous workflow, which published on every push to
`main`, was removed in Phase 6 (project-status finding S11). Merging a
pull request never publishes anything.

## Versioning

- The protocol version is **1.0** (`PROTOCOL_VERSION` in
  `e4a_sdk/schema.py`); it changes only with the specification.
- The package version lives in three places that must always agree:
  `pyproject.toml`, `sdk/python/e4a_sdk/__version__.py`, and
  `package.json` (the npm wrapper). As of Phase 6 all three read
  **1.0.1**. The final 1.0-release package version is a maintainer
  decision made at release-candidate time (Phase 9).

## Release procedure (maintainer)

1. **Prepare artifacts.** Run the *Release Preparation* workflow manually
   (GitHub Actions → "Release Preparation (manual, no publishing)" → Run
   workflow), or locally:
   ```bash
   python -m pytest tests/ -q
   python -m build
   python -m venv /tmp/e4a-clean && /tmp/e4a-clean/bin/pip install dist/*.whl
   cd /tmp && /tmp/e4a-clean/bin/python /path/to/repo/scripts/verify_installed_artifact.py
   ```
   All tests must pass and the artifact verification must print its OK
   lines. Inspect the workflow's `e4a-dist` artifact if run on GitHub.
2. **Decide and set the version** in the three places above; update
   `CHANGELOG.md` (move Unreleased entries into a versioned section).
3. **Tag** the release commit: `git tag v<version>` and push the tag.
4. **Publish** (only with explicit maintainer approval of the release
   candidate):
   ```bash
   python -m build
   twine upload dist/*        # PyPI (e4a-sdk)
   npm publish --access public  # npm wrapper (@e4aproject/protocol)
   ```
5. **Verify the published artifacts** from a clean environment against
   the public indexes (install, `e4a version`, quickstart lifecycle),
   and record the verification in `docs/project-status.md`.

## What is not automated, on purpose

- No push, merge, or tag triggers a publish.
- The semantic-release configuration that remains in `package.json` is
  legacy and is not invoked by any workflow; do not re-enable it without
  a maintainer decision recorded in `docs/project-status.md`.
