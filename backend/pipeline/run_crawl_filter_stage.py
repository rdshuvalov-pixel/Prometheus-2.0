"""python -m backend.pipeline.run_crawl_filter_stage

Applies the same rules as the legacy inline crawl filters to rows ingested as raw
(pipeline_status=CrawlRaw): keyword/title gate, post_collection_filter, dedup vs master `vacancies`.

Pass → pipeline_status=Staged (ready for enrich_texts).
Fail → pipeline_status=CrawlRejected + warnings.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.pipeline.crawl_constants import (
    PIPELINE_AFTER_CRAWL_FILTER,
    PIPELINE_CRAWL_RAW,
    PIPELINE_CRAWL_REJECTED,
)
from backend.pipeline.dedup import dedup_check, reapply_title_suffix
from backend.pipeline.filter.post_collection import post_collection_filter
from backend.pipeline.filter.search_time import passes_search_filters
from backend.pipeline.normalize.text import normalize_company, normalize_title


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_existing_company(cli, profile_id: str, company_normalized: str) -> list[dict]:
    res = (
        cli.table("vacancies")
        .select("id, company, role_title, posted_at")
        .eq("profile_id", profile_id)
        .eq("company_normalized", company_normalized)
        .execute()
    )
    return getattr(res, "data", None) or []


def _parse_posted_at(val: object) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            d = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _merge_warnings(existing: object, *codes: str) -> list[str]:
    cur = list(existing) if isinstance(existing, list) else []
    out = [*cur]
    for c in codes:
        if c not in out:
            out.append(c)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=50)
    p.add_argument("--delay", type=float, default=0.0)
    p.add_argument("--drain", action="store_true")
    p.add_argument("--profile-id", dest="profile_id", default=None)
    p.add_argument("--run-id", dest="run_id", default=None)
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    passed_n = 0
    rejected_n = 0

    while True:
        res = (
            cli.table("vacancies_stage")
            .select(
                "id, url, company, role_title, job_title, description, posted_at, warnings, "
                "company_normalized, role_title_normalized"
            )
            .eq("profile_id", profile_id)
            .eq("status", "Staged")
            .eq("pipeline_status", PIPELINE_CRAWL_RAW)
            .order("created_at", desc=False)
            .limit(max(1, int(args.batch)))
            .execute()
        )
        rows = getattr(res, "data", None) or []
        if not rows:
            out = {"passed": passed_n, "rejected": rejected_n}
            if args.run_id:
                merge_run_metrics(
                    args.run_id,
                    {"stage_crawl_filter_passed": passed_n, "stage_crawl_filter_rejected": rejected_n},
                )
            print(json.dumps(out, ensure_ascii=False))
            return

        for v in rows:
            sid = v.get("id")
            if not sid:
                continue
            now = _utc_iso()
            role_title = (v.get("job_title") or v.get("role_title") or "").strip()
            description = v.get("description") or ""
            loc_text = f"{role_title}\n{description[:2000]}"
            posted = _parse_posted_at(v.get("posted_at"))

            ok_search, search_reason = passes_search_filters(role_title, profile.search_keywords)
            if not ok_search:
                rejected_n += 1
                cli.table("vacancies_stage").update(
                    {
                        "pipeline_status": PIPELINE_CRAWL_REJECTED,
                        "warnings": _merge_warnings(v.get("warnings"), f"crawl_filter:{search_reason or 'search_role_excluded'}"),
                        "updated_at": now,
                    }
                ).eq("id", sid).execute()
                continue

            pf = post_collection_filter(
                role_title=role_title,
                description=description,
                location_text=loc_text,
                employment_type=None,
                posted_at=posted,
            )
            if not pf.passed:
                rejected_n += 1
                rr = pf.reject_reason or "unknown"
                cli.table("vacancies_stage").update(
                    {
                        "pipeline_status": PIPELINE_CRAWL_REJECTED,
                        "warnings": _merge_warnings(v.get("warnings"), f"crawl_filter:{rr}", *pf.warnings),
                        "updated_at": now,
                    }
                ).eq("id", sid).execute()
                continue

            cn = (v.get("company_normalized") or "").strip() or normalize_company(v.get("company") or "")
            existing = _fetch_existing_company(cli, profile_id, cn)
            dm = dedup_check(
                company=v.get("company") or "",
                role_title=role_title,
                existing_rows=existing,
                posted_at=posted,
            )
            if dm.is_duplicate:
                rejected_n += 1
                cli.table("vacancies_stage").update(
                    {
                        "pipeline_status": PIPELINE_CRAWL_REJECTED,
                        "warnings": _merge_warnings(v.get("warnings"), "crawl_filter:duplicate"),
                        "updated_at": now,
                    }
                ).eq("id", sid).execute()
                continue

            title_final = role_title
            if dm.is_reapply and dm.existing_id:
                title_final = reapply_title_suffix(role_title, posted)

            payload = {
                "pipeline_status": PIPELINE_AFTER_CRAWL_FILTER,
                "warnings": _merge_warnings(v.get("warnings"), *pf.warnings),
                "company_normalized": cn or normalize_company(v.get("company") or ""),
                "role_title": title_final,
                "job_title": title_final,
                "role_title_normalized": normalize_title(title_final),
                "updated_at": now,
            }

            cli.table("vacancies_stage").update(payload).eq("id", sid).execute()
            passed_n += 1
            if args.delay > 0:
                time.sleep(float(args.delay))

        if not args.drain:
            out = {"passed": passed_n, "rejected": rejected_n}
            if args.run_id:
                merge_run_metrics(
                    args.run_id,
                    {"stage_crawl_filter_passed": passed_n, "stage_crawl_filter_rejected": rejected_n},
                )
            print(json.dumps(out, ensure_ascii=False))
            return


if __name__ == "__main__":
    main()
