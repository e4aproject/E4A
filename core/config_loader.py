"""
Config loader for E4A projects.
Loads YAML config (config/config.yaml) and exposes a simple Config object.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

DEFAULT_PATH = Path(os.path.dirname(__file__)).parent.joinpath("config", "config.yaml")

class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def as_dict(self):
        return dict(self._data)

def load_config(path: str = None) -> Config:
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        # default config if none exists
        default = {
            "node_id": "e4a-node-1",
            "api": {"host": "http://localhost:8000", "timeout": 5},
            "db": {"type": "json", "path": "data/state.json"},
            "logging": {"level": "INFO"}
        }
        return Config(default)
    with open(p, "r") as fh:
        data = yaml.safe_load(fh) or {}
    return Config(data)
