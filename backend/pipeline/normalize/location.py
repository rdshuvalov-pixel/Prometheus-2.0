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


_hybrid_reject_locations_cache: list[str] | None = None


def _hybrid_reject_locations() -> list[str]:
    global _hybrid_reject_locations_cache
    if _hybrid_reject_locations_cache is not None:
        return _hybrid_reject_locations_cache
    if not _DATA.exists():
        _hybrid_reject_locations_cache = []
        return _hybrid_reject_locations_cache
    raw = yaml.safe_load(_DATA.read_text(encoding="utf-8"))
    _hybrid_reject_locations_cache = list(raw.get("hybrid_reject_locations", []))
    return _hybrid_reject_locations_cache


def hybrid_location_blacklisted(text: str) -> str | None:
    """Если в тексте упомянут hybrid и одна из локаций блэк-листа — вернуть имя локации."""
    low = text.lower()
    if "hybrid" not in low:
        return None
    for loc in _hybrid_reject_locations():
        if loc.lower() in low:
            return loc
    return None


def location_in_blacklist(text: str) -> str | None:
    """Любое упоминание локации из hybrid_reject_locations (Cyprus, Georgia, города)."""
    low = text.lower()
    for loc in _hybrid_reject_locations():
        if loc.lower() in low:
            return loc
    return None
