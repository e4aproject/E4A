#!/usr/bin/env python3
import json, hashlib, sys
from typing import Any
def canonicalize_and_hash(obj: Any) -> str:
    j = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(j.encode("utf-8")).hexdigest()
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m tools.mission_log_canonicalizer <json-file>")
        sys.exit(1)
    with open(sys.argv[1], "r") as f: obj = json.load(f)
    print(canonicalize_and_hash(obj))
