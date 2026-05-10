"""CLI: python -m backend.pipeline.run_crawl --tier 1"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import timezone
from pathlib import Path

import yaml
from backend.crawlers.ashby import ashby_org_slug, fetch_ashby_board
from backend.crawlers.breezy import breezy_slug, fetch_breezy
from backend.crawlers.greenhouse import board_token_from_url, fetch_greenhouse
from backend.crawlers.jobspy_crawler import fetch_jobspy_tier4
from backend.crawlers.lever import fetch_lever_board, slug_from_url
from backend.crawlers.playwright_generic import fetch_with_playwright
from backend.crawlers.workable import fetch_workable, short_from_url
from backend.db.client import apply_active_profile_id, finish_run, get_active_profile, insert_run, log_event
from backend.pipeline.crawl_alerts import record_failure
from backend.pipeline.dedup import dedup_check, reapply_title_suffix
from backend.pipeline.filter.post_collection import post_collection_filter
from backend.pipeline.filter.search_time import passes_search_filters
from backend.pipeline.crawl_constants import PIPELINE_CRAWL_RAW
from backend.pipeline.normalize.text import normalize_company, normalize_title
from backend.pipeline.raw_writer import persist_raw

_REPO = Path(__file__).resolve().parents[2]
_TARGETS = _REPO / "backend" / "sources" / "targets.yaml"


async def collect_for_target(t: dict, profile) -> list:
    company = t.get("company", "")
    url = t.get("url", "")
    tier = str(t.get("tier", "1"))
    ats = t.get("ats_type")
    raws: list = []
    if ats == "lever" and slug_from_url(url):
        raws = await fetch_lever_board(slug_from_url(url) or "", company, tier)
    elif ats == "greenhouse" and board_token_from_url(url):
        raws = await fetch_greenhouse(board_token_from_url(url) or "", company, tier)
    elif ats == "ashby" and ashby_org_slug(url):
        raws = await fetch_ashby_board(ashby_org_slug(url) or "", company, tier)
    elif ats == "workable" and short_from_url(url):
        raws = await fetch_workable(short_from_url(url) or "", company, tier)
    elif ats == "breezy" and breezy_slug(url):
        raws = await fetch_breezy(breezy_slug(url) or "", company, tier)
    else:
        raws = await fetch_with_playwright(url, company, tier)
    return raws


def _fetch_existing_company(cli, profile_id: str, company_normalized: str) -> list[dict]:
    if cli is None:
        return []
    res = (
        cli.table("vacancies")
        .select("id, company, role_title, posted_at")
        .eq("profile_id", profile_id)
        .eq("company_normalized", company_normalized)
        .execute()
    )
    return getattr(res, "data", None) or []


def insert_vacancy(cli, row: dict) -> bool:
    if cli is None:
        return True
    try:
        cli.table("vacancies").insert(row).execute()
        return True
    except Exception:
        return False


def insert_stage(cli, row: dict) -> bool:
    if cli is None:
        return True
    try:
        cli.table("vacancies_stage").insert(row).execute()
        return True
    except Exception:
        return False


async def main_async(args: argparse.Namespace) -> None:
    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None

    if args.tier == "4":
        run_id = insert_run(profile_id)
        log_event(
            run_id,
            "crawl_started",
            {"tier": "4", "source": "jobspy", "targets": 0, "targets_total_yaml": 0, "limit": args.limit},
        )
        rwanted = args.limit if args.limit and args.limit > 0 else 50
        raws = fetch_jobspy_tier4(profile.search_keywords, results_wanted=rwanted)
        processed = len(raws)
        kept = 0
        rejected = 0
        cli = __import__("backend.db.client", fromlist=["get_supabase"]).get_supabase()
        for rv in raws:
            persist_raw(rv)
            if args.to_stage and not args.filter_at_crawl:
                if not profile_id:
                    kept += 1
                    continue
                cn = normalize_company(rv.company)
                row_insert = {
                    "profile_id": profile_id,
                    "company": rv.company,
                    "company_name": rv.company,
                    "role_title": rv.title,
                    "job_title": rv.title,
                    "role_title_normalized": normalize_title(rv.title),
                    "company_normalized": cn,
                    "url": rv.url,
                    "job_url": rv.url,
                    "description": rv.description,
                    "run_id": run_id,
                    "status": "Staged",
                    "pipeline_status": PIPELINE_CRAWL_RAW,
                    "posted_at": rv.posted_at.isoformat() if rv.posted_at else None,
                    "warnings": [],
                }
                if insert_stage(cli, row_insert):
                    kept += 1
                else:
                    rejected += 1
                continue

            ok_s, _ = passes_search_filters(rv.title, profile.search_keywords)
            if not ok_s:
                rejected += 1
                continue
            loc = f"{rv.location}\n{rv.description[:2000]}"
            pf = post_collection_filter(
                role_title=rv.title,
                description=rv.description,
                location_text=loc,
                employment_type=rv.employment_type,
                posted_at=rv.posted_at,
            )
            if not pf.passed:
                rejected += 1
                continue
            row_insert = {
                "profile_id": profile_id,
                "company": rv.company,
                "company_name": rv.company,
                "role_title": rv.title,
                "job_title": rv.title,
                "role_title_normalized": normalize_title(rv.title),
                "company_normalized": normalize_company(rv.company),
                "url": rv.url,
                "job_url": rv.url,
                "description": rv.description,
                **({"run_id": run_id, "status": "Staged", "pipeline_status": "Staged"} if args.to_stage else {"status": "New"}),
                "posted_at": rv.posted_at.isoformat() if rv.posted_at else None,
                "warnings": pf.warnings,
            }
            if profile_id and (insert_stage(cli, row_insert) if args.to_stage else insert_vacancy(cli, row_insert)):
                kept += 1
        metrics = {"processed": processed, "kept": kept, "rejected": rejected}
        if run_id:
            finish_run(run_id, "ok", metrics)
        print(json.dumps(metrics, ensure_ascii=False))
        return

    if not _TARGETS.exists():
        print(json.dumps({"error": "Run backend.scripts.build_targets first", "targets": 0}))
        return

    data = yaml.safe_load(_TARGETS.read_text(encoding="utf-8"))
    tier_filter = args.tier
    all_targets = data.get("targets", [])
    targets = [t for t in all_targets if tier_filter in ("all", str(t.get("tier")))]
    slice_targets = targets if args.limit == 0 else targets[: args.limit]

    run_id = insert_run(profile_id)
    log_event(
        run_id,
        "crawl_started",
        {
            "tier": tier_filter,
            "targets": len(targets),
            "targets_total_yaml": len(all_targets),
            "limit": args.limit,
            "slice": len(slice_targets),
        },
    )

    from backend.db.client import get_supabase

    cli = get_supabase()
    processed = 0
    kept = 0
    rejected = 0

    async def process_target(t: dict) -> tuple[int, int, int]:
        company_name = t.get("company") or ""
        t0 = time.perf_counter()
        log_event(
            run_id,
            "target_started",
            {
                "company": company_name,
                "url": t.get("url"),
                "ats": t.get("ats_type"),
                "tier": str(t.get("tier")),
            },
        )

        target_processed = 0
        target_kept = 0
        target_rejected = 0
        target_rejects: dict[str, int] = {}
        errored = False

        try:
            raws = await asyncio.wait_for(
                collect_for_target(t, profile),
                timeout=max(1, int(args.target_timeout_s)),
            )
        except TimeoutError:
            errored = True
            raws = []
            log_event(
                run_id,
                "crawl_error",
                {"company": company_name, "error": f"target_timeout_{int(args.target_timeout_s)}s"},
                level="error",
            )
            record_failure(normalize_company(company_name), run_id)
        except Exception as e:
            errored = True
            raws = []
            log_event(run_id, "crawl_error", {"company": company_name, "error": str(e)}, level="error")
            record_failure(normalize_company(company_name), run_id)

        for rv in raws:
            target_processed += 1
            persist_raw(rv)
            if args.to_stage and not args.filter_at_crawl:
                if not profile_id:
                    target_kept += 1
                    continue
                cn = normalize_company(rv.company)
                row_insert = {
                    "profile_id": profile_id,
                    "company": rv.company,
                    "company_name": rv.company,
                    "role_title": rv.title,
                    "job_title": rv.title,
                    "role_title_normalized": normalize_title(rv.title),
                    "company_normalized": cn,
                    "url": rv.url,
                    "job_url": rv.url,
                    "description": rv.description,
                    "run_id": run_id,
                    "status": "Staged",
                    "pipeline_status": PIPELINE_CRAWL_RAW,
                    "posted_at": rv.posted_at.isoformat() if rv.posted_at else None,
                    "warnings": [],
                }
                if insert_stage(cli, row_insert):
                    target_kept += 1
                else:
                    target_rejected += 1
                    target_rejects["insert_failed"] = target_rejects.get("insert_failed", 0) + 1
                    log_event(
                        run_id,
                        "vacancy_rejected",
                        {"company": rv.company, "title": rv.title[:200], "reason": "insert_failed"},
                    )
                continue

            ok_search, _ = passes_search_filters(rv.title, profile.search_keywords)
            if not ok_search:
                target_rejected += 1
                target_rejects["search_role_excluded"] = target_rejects.get("search_role_excluded", 0) + 1
                log_event(
                    run_id,
                    "vacancy_rejected",
                    {"company": rv.company, "title": rv.title[:200], "reason": "search_role_excluded"},
                )
                continue
            loc_text = f"{rv.location}\n{rv.description[:2000]}"
            pf = post_collection_filter(
                role_title=rv.title,
                description=rv.description,
                location_text=loc_text,
                employment_type=rv.employment_type,
                posted_at=rv.posted_at,
            )
            if not pf.passed:
                target_rejected += 1
                rr = pf.reject_reason or "unknown"
                target_rejects[rr] = target_rejects.get(rr, 0) + 1
                log_event(
                    run_id,
                    "vacancy_rejected",
                    {
                        "company": rv.company,
                        "title": rv.title[:200],
                        "reason": rr,
                        "warnings": pf.warnings,
                    },
                )
                continue
            if not profile_id:
                target_kept += 1
                continue
            cn = normalize_company(rv.company)
            existing = _fetch_existing_company(cli, profile_id, cn)
            posted = rv.posted_at
            if posted and posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            dm = dedup_check(
                company=rv.company,
                role_title=rv.title,
                existing_rows=existing,
                posted_at=posted,
            )
            if dm.is_duplicate:
                target_rejected += 1
                target_rejects["duplicate"] = target_rejects.get("duplicate", 0) + 1
                log_event(
                    run_id,
                    "vacancy_rejected",
                    {"company": rv.company, "title": rv.title[:200], "reason": "duplicate"},
                )
                continue
            title_final = rv.title
            prev_id = None
            if dm.is_reapply and dm.existing_id:
                title_final = reapply_title_suffix(rv.title, posted)
                prev_id = dm.existing_id
            row_insert = {
                "profile_id": profile_id,
                "company": rv.company,
                "company_name": rv.company,
                "role_title": title_final,
                "job_title": title_final,
                "role_title_normalized": normalize_title(title_final),
                "company_normalized": cn,
                "url": rv.url,
                "job_url": rv.url,
                "description": rv.description,
                **({"run_id": run_id, "status": "Staged", "pipeline_status": "Staged"} if args.to_stage else {"status": "New"}),
                "posted_at": rv.posted_at.isoformat() if rv.posted_at else None,
                "warnings": pf.warnings,
            }
            if prev_id:
                row_insert["previous_vacancy_id"] = prev_id
            if (insert_stage(cli, row_insert) if args.to_stage else insert_vacancy(cli, row_insert)):
                target_kept += 1
            else:
                target_rejected += 1
                target_rejects["insert_failed"] = target_rejects.get("insert_failed", 0) + 1
                log_event(
                    run_id,
                    "vacancy_rejected",
                    {"company": rv.company, "title": rv.title[:200], "reason": "insert_failed"},
                )

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        print(
            json.dumps(
                {
                    "event": "target_done",
                    "company": company_name,
                    "raws": len(raws),
                    "processed": target_processed,
                    "kept": target_kept,
                    "rejected": target_rejected,
                    "elapsed_ms": elapsed_ms,
                    "errored": errored,
                },
                ensure_ascii=False,
            )
        )
        log_event(
            run_id,
            "target_done",
            {
                "company": company_name,
                "raws": len(raws),
                "kept": target_kept,
                "rejected": target_rejected,
                "by_reason": target_rejects,
                "errored": errored,
                "elapsed_ms": elapsed_ms,
            },
        )
        return (target_processed, target_kept, target_rejected)

    q: asyncio.Queue[dict | None] = asyncio.Queue()
    for t in slice_targets:
        q.put_nowait(t)
    workers_n = max(1, int(args.concurrency))
    for _ in range(workers_n):
        q.put_nowait(None)

    async def worker() -> None:
        nonlocal processed, kept, rejected
        while True:
            t = await q.get()
            try:
                if t is None:
                    return
                tp, tk, tr = await process_target(t)
                processed += tp
                kept += tk
                rejected += tr
            finally:
                q.task_done()

    await asyncio.gather(*(worker() for _ in range(workers_n)))

    metrics = {"processed": processed, "kept": kept, "rejected": rejected}
    if run_id:
        finish_run(run_id, "ok", metrics)
    log_event(run_id, "crawl_finished", metrics)
    print(json.dumps(metrics, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", default="1", help="1,2,3,4 или all")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Число целей tier (0 = без ограничения, обходит все)",
    )
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel targets to crawl")
    parser.add_argument("--target-timeout-s", dest="target_timeout_s", type=int, default=120, help="Timeout per target")
    parser.add_argument("--profile-id", dest="profile_id", default=None, help="UUID профиля candidate_profiles")
    parser.add_argument("--to-stage", action="store_true", help="Писать результаты в vacancies_stage вместо vacancies")
    parser.add_argument(
        "--filter-at-crawl",
        action="store_true",
        help="Вместе с --to-stage: применять фильтры сразу при крауле (старое поведение). "
        "Без этого флага в stage пишется сырое CrawlRaw, фильтр — отдельным шагом run_crawl_filter_stage.",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
