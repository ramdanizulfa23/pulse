"""Pulse configuration loader.

Reads ``config.json`` (installed next to the package under
``${datadir}/nusa/``) and merges it over the module defaults. The result
is a plain dict-like object with attribute access.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "mode": "gtk",
    "zoom": 1.0,
    "music_dir": str(BASE_DIR / "resources" / "data" / "music"),
    "lyrics": "on",
    "timer": "off",
    "volume": "on",
    "cat_eyes": "on",
    "show_playlist": "on",
}

_ON = {"1", "on", "true", "yes", "enable"}

def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in _ON

def _as_zoom(value: object) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 1.0
    return max(0.5, min(1.6, v))

class Config(dict):
    """Mutable config bag with attribute-style access."""

    def __init__(self, overrides: dict | None = None) -> None:
        super().__init__()
        self.update(DEFAULTS)
        self.update(_load_file())
        if overrides:
            self.update(overrides)

    def __getattr__(self, key: str) -> object:
        try:
            return super().__getitem__(key)
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: object) -> None:
        self[key] = value

    def update(self, overrides: dict) -> None:
        for key, value in overrides.items():
            if key not in DEFAULTS:
                self[key] = value
                continue
            if key == "mode":
                self[key] = str(value).strip().lower()
            elif key == "zoom":
                self[key] = _as_zoom(value)
            elif key in {"lyrics", "timer", "volume", "cat_eyes", "show_playlist"}:
                self[key] = _as_bool(value)
            else:
                self[key] = value

    def is_on(self, key: str) -> bool:
        return bool(self.get(key, False))

def _load_file() -> dict:
    path = BASE_DIR / "config.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        print(f"[Pulse] config read failed: {exc}", flush=True)
        return {}
    merged: dict = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k in DEFAULTS})
    merged["zoom"] = _as_zoom(merged.get("zoom", 1.0))
    return merged

config: Config = Config()
