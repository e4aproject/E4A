# Publishing E4A Packages

This document describes the automated process for publishing the e4a packages to PyPI and NPM.

## Release Process

Publication is handled automatically via the `.github/workflows/release.yml` GitHub Action whenever a new release is created in the GitHub repository.

## Authentication

We use **OIDC (OpenID Connect)** for authentication with PyPI, which is the current industry best practice for security. This method avoids the need to store long-lived API tokens like `PYPI_API_TOKEN` as repository secrets.

For NPM, we will continue to use an `NPM_TOKEN` stored in repository secrets until OIDC support is fully stabilized and adopted by `semantic-release`.

## Steps to Release

1.  Ensure all changes for the release are merged into the `main` branch.
2.  Navigate to the "Releases" page of the GitHub repository.
3.  Draft a new release, creating a new tag that follows semantic versioning (e.g., `v1.1.0`).
4.  Write clear release notes describing the changes.
5.  Publish the release.

The GitHub Action will automatically trigger, build the packages, and publish them to their respective registries.
