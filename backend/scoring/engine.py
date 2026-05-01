from __future__ import annotations

from typing import Any

from backend.scoring.loader import load_weights


def _sum_group(
    features: dict[str, Any],
    group_name: str,
    weights: dict[str, Any],
    *,
    require_true_value: bool = False,
) -> tuple[float, dict[str, Any]]:
    g_feat = features.get(group_name) or {}
    g_w = weights.get(group_name) or {}
    total = 0.0
    breakdown: dict[str, Any] = {}
    for key, w in g_w.items():
        entry = g_feat.get(key) or {}
        if require_true_value and not entry.get("value", False):
            breakdown[key] = {"points": 0.0, "max": w, "evidence": entry.get("evidence") or []}
            continue
        pts = float(entry.get("points") or 0)
        capped = min(pts, float(w))
        total += capped
        breakdown[key] = {"points": capped, "max": w, "evidence": entry.get("evidence") or []}
    return total, breakdown


def compute_score(
    features: dict[str, Any],
    weights_override: dict[str, Any] | None = None,
) -> tuple[int, bool, dict[str, Any]]:
    """
    Возвращает (score 0..100, group_a_passed, full_breakdown).
    Если группа A не пройдена — итог cap 49.
    """
    weights = load_weights(weights_override)
    crit = features.get("critical") or {}
    a_keys = list((weights.get("critical") or {}).keys())
    group_a_passed = True
    for k in a_keys:
        entry = crit.get(k) or {}
        val = entry.get("value")
        if val is False:
            group_a_passed = False
            break

    total_a, bd_a = _sum_group(features, "critical", weights, require_true_value=True)
    total_b, bd_b = _sum_group(features, "experience", weights)
    total_c, bd_c = _sum_group(features, "skills", weights)
    total_d, bd_d = _sum_group(features, "strategy_growth", weights)
    total_e, bd_e = _sum_group(features, "company_context", weights)
    total_f, bd_f = _sum_group(features, "bonuses", weights)

    raw = total_a + total_b + total_c + total_d + total_e + total_f
    if not group_a_passed:
        score = min(round(raw), 49)
    else:
        score = min(round(raw), 100)

    breakdown = {
        "critical": bd_a,
        "experience": bd_b,
        "skills": bd_c,
        "strategy_growth": bd_d,
        "company_context": bd_e,
        "bonuses": bd_f,
        "group_a_passed": group_a_passed,
        "raw_total": raw,
    }
    return score, group_a_passed, breakdown


def match_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Weak"
    return "Rejected"
