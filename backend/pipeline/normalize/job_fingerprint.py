"""Semantic job fingerprint per docs/llm_prompt.md §16."""

from __future__ import annotations

import hashlib


def compute_job_fingerprint(
    *,
    company_normalized: str,
    normalized_title: str | None,
    seniority: str | None,
    function: str | None,
    country: str | None,
    location_normalized: str | None,
) -> str:
    parts = [
        company_normalized or "",
        normalized_title or "",
        seniority or "",
        function or "",
        country or "",
        location_normalized or "",
    ]
    value = "|".join((p or "").lower().strip() for p in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
