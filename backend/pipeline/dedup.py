from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.pipeline.normalize.text import normalize_company, normalize_title
from rapidfuzz import fuzz


@dataclass
class DedupMatch:
    is_duplicate: bool
    existing_id: str | None
    is_reapply: bool


def fuzzy_same_role(a: str, b: str, threshold: int = 90) -> bool:
    return fuzz.token_set_ratio(normalize_title(a), normalize_title(b)) >= threshold


def dedup_check(
    *,
    company: str,
    role_title: str,
    existing_rows: list[dict],
    posted_at: datetime | None,
    reapply_days: int = 30,
) -> DedupMatch:
    """existing_rows: [{id, role_title, posted_at}] для того же profile."""
    nc = normalize_company(company)
    for row in existing_rows:
        if normalize_company(row.get("company", "")) != nc:
            continue
        if not fuzzy_same_role(role_title, row.get("role_title", "")):
            continue
        old_posted = row.get("posted_at")
        if isinstance(old_posted, str):
            old_posted = datetime.fromisoformat(old_posted.replace("Z", "+00:00"))
        if posted_at and old_posted:
            if posted_at.replace(tzinfo=timezone.utc) > old_posted.replace(
                tzinfo=timezone.utc
            ) + timedelta(days=reapply_days):
                return DedupMatch(False, str(row["id"]), True)
        return DedupMatch(True, str(row["id"]), False)
    return DedupMatch(False, None, False)


def reapply_title_suffix(role_title: str, when: datetime | None = None) -> str:
    when = when or datetime.now(timezone.utc)
    d = when.strftime("%Y-%m-%d")
    return f"{role_title} [reapply {d}]"
