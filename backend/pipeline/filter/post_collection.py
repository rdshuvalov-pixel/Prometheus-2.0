from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.pipeline.normalize.date_parse import is_stale
from backend.pipeline.normalize.location import (
    detect_hybrid_lisbon,
    location_signals_eu_or_global,
    location_signals_reject_region,
)
from backend.pipeline.normalize.role import is_product_title
from backend.pipeline.normalize.seniority import detect_seniority
from backend.pipeline.normalize.work_format import detect_work_format


@dataclass
class PostCollectionResult:
    passed: bool
    reject_reason: str | None
    warnings: list[str]


def post_collection_filter(
    *,
    role_title: str,
    description: str,
    location_text: str,
    employment_type: str | None,
    posted_at: datetime | None,
    hybrid_lisbon_only: bool = True,
) -> PostCollectionResult:
    warnings: list[str] = []
    full_text = f"{role_title}\n{description}\n{location_text}"

    if not is_product_title(role_title, description):
        return PostCollectionResult(False, "not_product_role", warnings)

    seniority = detect_seniority(role_title, description)
    if seniority == "junior":
        return PostCollectionResult(False, "not_product_role", warnings)

    wf = detect_work_format(full_text)
    hybrid_lisbon = detect_hybrid_lisbon(full_text)

    if wf == "office":
        return PostCollectionResult(False, "office_only", warnings)

    if wf == "hybrid" and hybrid_lisbon_only and not hybrid_lisbon:
        return PostCollectionResult(False, "hybrid_outside_lisbon", warnings)

    if location_signals_reject_region(full_text):
        return PostCollectionResult(False, "us_only", warnings)

    if wf == "remote" or wf == "hybrid":
        if not location_signals_eu_or_global(full_text) and not hybrid_lisbon:
            if "unknown" in full_text.lower():
                warnings.append("location_ambiguous")
            else:
                return PostCollectionResult(False, "us_only", warnings)

    et = (employment_type or "").lower()
    if et:
        if any(x in et for x in ("part", "fractional", "contract")) and "long" not in et:
            if "full" not in et:
                return PostCollectionResult(False, "part_time", warnings)
    else:
        warnings.append("employment_type_unknown")

    if posted_at is not None:
        if is_stale(posted_at):
            return PostCollectionResult(False, "expired_or_old", warnings)
    else:
        warnings.append("date_unknown")

    return PostCollectionResult(True, None, warnings)
