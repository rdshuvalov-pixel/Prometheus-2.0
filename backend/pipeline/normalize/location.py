from __future__ import annotations

import re
from pathlib import Path

import yaml

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_DATA = _BACKEND_ROOT / "sources" / "eu_countries.yaml"


def _keywords() -> tuple[list[str], list[str]]:
    if not _DATA.exists():
        return (
            ["EU", "Europe", "EMEA", "Portugal", "Lisbon", "Worldwide", "Global"],
            ["US-only", "USA only", "Canada only"],
        )
    raw = yaml.safe_load(_DATA.read_text(encoding="utf-8"))
    return list(raw.get("eu_keywords", [])), list(raw.get("reject_country_only", []))


def location_signals_eu_or_global(text: str) -> bool:
    eu_kw, _ = _keywords()
    t = text.lower()
    for k in eu_kw:
        if k.lower() in t:
            return True
    if re.search(r"(?i)\b(remote\s+(europe|eu|emea)|eu\s+remote|emea)\b", text):
        return True
    return False


def location_signals_reject_region(text: str) -> bool:
    _, rej = _keywords()
    lower = text.lower()
    if re.search(r"(?i)\b(us|united states)[-\s]?only\b", text):
        return True
    if re.search(r"(?i)\bcanada[-\s]?only\b", text):
        return True
    if re.search(r"(?i)\buk[-\s]?only\b", text) and "right to work" in lower:
        return True
    for k in rej:
        if k.lower() in lower:
            return True
    return False


def detect_hybrid_lisbon(text: str) -> bool:
    return bool(re.search(r"(?i)lisbon", text)) and bool(re.search(r"(?i)hybrid", text))
