"""Сравнение скоринга с базовыми весами и overrides (страница /profile preview)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.scoring.engine import compute_score

_REPO = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).resolve().parent / "preview_fixtures.json"


def _default_fixtures() -> list[dict[str, Any]]:
    path = _FIXTURES
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("fixtures", []))
    return [
        {
            "id": "baseline_pass",
            "features": {
                "critical": {
                    "product_management": {"value": True, "points": 10, "evidence": []},
                    "work_format_fit": {"value": True, "points": 10, "evidence": []},
                    "seniority_fit": {"value": True, "points": 10, "evidence": []},
                    "full_time": {"value": True, "points": 5, "evidence": []},
                    "location_fit": {"value": True, "points": 5, "evidence": []},
                },
                "experience": {
                    "fintech_or_ecommerce": {"points": 6, "evidence": []},
                    "b2b_saas": {"points": 5, "evidence": []},
                },
                "skills": {},
                "strategy_growth": {},
                "company_context": {},
                "bonuses": {},
            },
        },
    ]


def compare_overrides(scoring_overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Возвращает score до/после для каждого fixture."""
    fixtures = _default_fixtures()
    rows = []
    for fx in fixtures:
        feats = fx.get("features") or {}
        fid = str(fx.get("id", "unknown"))
        score_before, _, _ = compute_score(feats, None)
        score_after, _, _ = compute_score(feats, scoring_overrides)
        rows.append(
            {
                "id": fid,
                "score_before": score_before,
                "score_after": score_after,
                "delta": score_after - score_before,
            }
        )
    return {"fixtures": rows}

