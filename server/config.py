"""
config.py – simple JSON‐based configuration helper
Stores / retrieves global settings such as API_KEY, MODEL, LANG, API_PROVIDER.
File saved at project root as settings.json
"""

import json
import os
from pathlib import Path

CFG_FILE = Path(__file__).resolve().parent.parent / "settings.json"

def _load() -> dict:
    """Load settings.json – return empty dict if missing / corrupt"""
    if CFG_FILE.exists():
        try:
            with open(CFG_FILE, "r", encoding="utf8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save(data: dict) -> None:
    """Persist dict to settings.json (pretty-printed)"""
    with open(CFG_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---- public helpers ---------------------------------------------------------

def get_config() -> dict:
    """Return full configuration dict"""
    return _load()

def set_config(key: str, value):
    """Set single key → value and save to disk"""
    cfg = _load()
    cfg[key] = value
    _save(cfg)

def update_config(new_data: dict):
    """Merge multiple keys, save"""
    cfg = _load()
    cfg.update(new_data)
    _save(cfg)

