"""Учёт падений краулера по компании (3 подряд → pipeline_events + disabled)."""

from __future__ import annotations

from backend.db.client import get_supabase, log_event


def record_failure(company_normalized: str, run_id: str | None) -> None:
    cli = get_supabase()
    if cli is None:
        return
    res = (
        cli.table("crawl_company_failures")
        .select("*")
        .eq("company_normalized", company_normalized)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    if not rows:
        cli.table("crawl_company_failures").insert(
            {
                "company_normalized": company_normalized,
                "fail_count": 1,
                "last_failed_at": now,
                "disabled": False,
            }
        ).execute()
        return
    fc = int(rows[0].get("fail_count") or 0) + 1
    disabled = fc >= 3
    cli.table("crawl_company_failures").update(
        {"fail_count": fc, "last_failed_at": now, "disabled": disabled}
    ).eq("company_normalized", company_normalized).execute()
    if disabled:
        log_event(
            run_id,
            "crawl_disabled",
            {"company": company_normalized, "fail_count": fc},
            level="error",
        )
