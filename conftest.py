"""Repository test configuration.

Makes the SDK package (sdk/python) and the repository-root packages
(api, adapters, cli, tools) importable when running pytest from a source
checkout, without requiring PYTHONPATH to be set. This matches how the
suite is documented to run; the packaged distribution does not rely on
this file.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
for _p in (str(ROOT), str(ROOT / "sdk" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
