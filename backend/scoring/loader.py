from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_weights(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "weights.yaml"
    base = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not overrides:
        return base
    merged: dict[str, Any] = dict(base)
    for group, weights in overrides.items():
        if isinstance(weights, dict) and isinstance(merged.get(group), dict):
            mg = dict(merged[group])
            mg.update({k: int(v) if isinstance(v, (int, float)) else v for k, v in weights.items()})
            merged[group] = mg
        else:
            merged[group] = weights
    return merged
