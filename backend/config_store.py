"""
Vesper — persistent JSON config store.
All settings are saved to /app/data/config.json (or CONFIG_PATH env var).
No .env editing required — everything is configured through the UI.
"""
import json
import copy
import os
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "/app/data/config.json"))

DEFAULTS: dict = {
    "proxmox": {
        "host": "",
        "port": 8006,
        "user": "root@pam",
        "password": "",
        "verify_ssl": False,
        "node": "pve",
    },
    "weather": {
        "api_key": "",
        "city": "",
        "units": "metric",
    },
    "calendar": {
        "ical_url": "",
    },
    "feeds": {
        "urls": "",
    },
    "services": {
        "list": "",
    },
    "gmail": {
        "client_id": "",
        "client_secret": "",
        "refresh_token": "",
    },
    "todos": {
        "items": [],
    },
}


def load() -> dict:
    """Load config from disk, merged with defaults."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                saved = json.load(f)
            result = copy.deepcopy(DEFAULTS)
            for k, v in saved.items():
                if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                    result[k].update(v)
                else:
                    result[k] = v
            return result
        except Exception:
            pass
    return copy.deepcopy(DEFAULTS)


def save(cfg: dict) -> None:
    """Write config to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def is_configured(section: str, *keys: str) -> bool:
    """Check if one or more keys in a section are non-empty."""
    cfg = load()
    sec = cfg.get(section, {})
    return all(bool(sec.get(k)) for k in keys)
