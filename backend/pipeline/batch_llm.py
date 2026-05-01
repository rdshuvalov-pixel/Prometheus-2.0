"""Пакетная подсказка для extract_scoring_features (несколько JD в одном промпте) — расширение Phase 7."""

from __future__ import annotations

from typing import Any


def build_batch_prompt(blocks: list[str]) -> str:
    parts = []
    for i, b in enumerate(blocks):
        parts.append(f"---JOB{i}---\n{b[:6000]}")
    return "\n".join(parts)


def stub_parse_batch_response(_content: str) -> list[dict[str, Any]]:
    """Устарело: см. `extract_scoring_features_batch` в `extract_scoring_features.py`."""
    return []
