"""
Canonical schema loading for E4A 1.0.

Schemas ship inside the package (``e4a_sdk/schemas/``) so the installed
artifact is self-contained. This replaces the prototype behavior of loading
``specs/*.json`` from the repository tree via relative paths, which made the
installed package unusable (project-status finding S3 / baseline B6).

The normative schema source is ``docs/protocol/mandate.schema.json``; the
bundled copy must be kept byte-identical in content (a test asserts this).
"""

import json
from pathlib import Path

_SCHEMA_DIR = Path(__file__).parent / "schemas"

PROTOCOL_VERSION = "1.0"


def _load(name):
    with open(_SCHEMA_DIR / name, "r") as fh:
        return json.load(fh)


MANDATE_SCHEMA = _load("mandate-1.0.json")
GATE_SCHEMA = _load("gate-1.0.json")
