#!/usr/bin/env python3
import json, jsonschema, sys
def validate_file(schema_path: str, data_path: str) -> int:
    try:
        with open(schema_path, "r") as f: schema = json.load(f)
        with open(data_path, "r") as f: data = json.load(f)
        jsonschema.validate(instance=data, schema=schema)
        print(f"✔ VALID: {data_path} conforms to {schema_path}")
        return 0
    except Exception as e:
        print(f"✘ INVALID: {data_path} failed validation: {e}")
        return 1
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m tools.validator <schema.json> <data.json>")
        sys.exit(2)
    sys.exit(validate_file(sys.argv[1], sys.argv[2]))
