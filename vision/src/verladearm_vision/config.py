"""Laden der YAML-Konfiguration.

Eine Anlagendatei kann mit `extends: <pfad>` auf eine Basisdatei verweisen (relativ zur
Anlagendatei). Werte der Anlagendatei überschreiben die Basis; Unterabschnitte werden
zusammengeführt, Listen ersetzt.
"""

from pathlib import Path

import yaml


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    parent = cfg.pop("extends", None)
    if parent:
        cfg = _merge(load_config(path.parent / parent), cfg)
    return cfg
