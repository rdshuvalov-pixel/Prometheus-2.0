"""python -m backend.pipeline.run_enrich — LLM enrich New vacancies."""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timedelta, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.llm.functions.classify_location import classify_location
from backend.llm.functions.extract_role_semantics import extract_role_semantics


def _merge_warnings(existing: object, *codes: str) -> list[str]:
    cur = list(existing) if isinstance(existing, list) else []
    out = [*cur]
    for c in codes:
        if c not in out:
            out.append(c)
    return out


def _since_start_iso(arg: str | None) -> str:
    if arg:
        parts = arg.strip().split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime(y, m, d, tzinfo=timezone.utc).isoformat()
    today = datetime.now(timezone.utc).date()
    start_day_utc = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) - timedelta(days=7)
    return start_day_utc.isoformat()


async def enrich_one(v: dict, run_id: str | None, rps_delay: float) -> None:
    desc = (v.get("description") or "").strip()
    cli = get_supabase()
    if cli is None:
        return

    if len(desc) < 100:
        cli.table("vacancies").update(
            {
                "enrichment_at": datetime.now(timezone.utc).isoformat(),
                "warnings": _merge_warnings(v.get("warnings"), "short_description"),
            }
        ).eq("id", v["id"]).execute()
        await asyncio.sleep(rps_delay)
        return

    text = f"{v.get('role_title', '')}\n{v.get('description', '')}"
    loc = await classify_location(text, run_id=run_id, vacancy_id=str(v.get("id")))
    role = await extract_role_semantics(text, run_id=run_id, vacancy_id=str(v.get("id")))
    evidence = {
        "location": loc.model_dump(),
        "role": role.model_dump(),
    }
    cli.table("vacancies").update(
        {
            "normalized_work_format": loc.work_format,
            "normalized_location": "eu" if loc.eu_compatible else "non_eu",
            "enrichment_at": datetime.now(timezone.utc).isoformat(),
            "evidence": evidence,
        }
    ).eq("id", v["id"]).execute()
    await asyncio.sleep(rps_delay)


async def main_async(args: argparse.Namespace) -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Set OPENROUTER_API_KEY")
        return
    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None:
        print("No Supabase; skip")
        return
    since_iso = _since_start_iso(args.since)
    enriched = 0
    while True:
        q = (
            cli.table("vacancies")
            .select("id, role_title, description, status, warnings, created_at")
            .eq("status", "New")
            .is_("enrichment_at", "null")
            .gte("created_at", since_iso)
            .order("created_at", desc=False)
            .limit(args.batch)
        )
        if profile_id:
            q = q.eq("profile_id", profile_id)
        res = q.execute()
        rows = getattr(res, "data", None) or []
        if not rows:
            if args.run_id:
                merge_run_metrics(args.run_id, {"enriched": enriched})
            return
        for v in rows:
            await enrich_one(v, args.run_id, args.rps)
            enriched += 1
        if not args.drain:
            if args.run_id:
                merge_run_metrics(args.run_id, {"enriched": enriched})
            return


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=20)
    # NOTE: name kept for backwards compatibility; value is a per-item delay in seconds.
    p.add_argument("--rps", type=float, default=0.2)
    p.add_argument("--run_id", default=None, help="pipeline_runs.id to attach metrics/events")
    p.add_argument("--drain", action="store_true", help="Process batches until queue is empty")
    p.add_argument(
        "--since",
        default=None,
        metavar="YYYY-MM-DD",
        help="Обрабатывать только vacancies с created_at >= этой даты UTC (по умолчанию — последние 7 дней, UTC)",
    )
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
