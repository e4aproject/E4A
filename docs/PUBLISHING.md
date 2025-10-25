# Publishing guide — E4A

This document describes the secrets and local commands used to publish the project to npm and PyPI. The repository includes a GitHub Actions workflow at `.github/workflows/publish.yml` that performs both steps when a change is pushed to `main` or the workflow is triggered manually.

Required GitHub Secrets

- `NPM_TOKEN` — an npm automation token with publish rights for the `@e4aproject` scope. Create it at https://www.npmjs.com/settings/<your-username>/tokens. In the workflow it is used to authenticate `semantic-release`.
- `PYPI_API_TOKEN` — a PyPI API token. Create it at https://pypi.org/manage/account/ (or the project-specific publisher page) and add it to the repository secrets. The action uses `__token__` as the username and this token as the password.
- `GITHUB_TOKEN` — provided automatically by GitHub Actions (no manual setup required).

Notes and recommendations

- Scoped npm packages (those whose `name` begins with `@e4aproject/`) are private by default. This repo sets `publishConfig.access = public` in `package.json` so the automated publish will attempt a public publish. Ensure the account that created `NPM_TOKEN` has permission to publish under `@e4aproject`.
- If your organization enforces npm 2FA restrictions, create a token set for CI/automation (Authorization-only token) and ensure that token is used for the `NPM_TOKEN` secret.

Local test commands

1. Check what npm would publish (dry-run):

```bash
npm publish --access public --dry-run
```

2. Build Python artifacts locally and verify them with twine:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

3. To upload to TestPyPI (manual, for testing) using an API token:

```bash
python -m twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p <TEST_PYPI_API_TOKEN> dist/*
```

CI behavior

- The workflow first runs `semantic-release` which will examine commits, determine a new version, publish to npm (via `@semantic-release/npm`), push tags, and create a GitHub Release with changelog.
- After `semantic-release` completes, the workflow builds Python distributions and uses `pypa/gh-action-pypi-publish` to upload to PyPI using `PYPI_API_TOKEN`.

Troubleshooting

- If semantic-release fails to publish to npm, check that `NPM_TOKEN` is set and belongs to an account with publish permissions for the `@e4aproject` scope.
- If PyPI upload fails, check `PYPI_API_TOKEN` and visit https://pypi.org/manage/project/<your-project>/settings/publishing/ to confirm GitHub Publisher settings if you are using the GitHub-to-PyPI publisher integration.

If you want, I can further refine the workflow to use OIDC (no stored secrets for PyPI) or split npm and PyPI into separate workflows with more granular permissions. Request that and I'll implement it.
