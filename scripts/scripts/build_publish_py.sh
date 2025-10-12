#!/usr/bin/env bash
set -e
python -m pip install --upgrade build
python -m build
echo "Built packages in dist/ — use twine to upload to PyPI when ready."
