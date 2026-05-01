"""python -m backend.pipeline.run_enrich — LLM enrich New vacancies."""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase
from backend.llm.functions.classify_location import classify_location
from backend.llm.functions.extract_role_semantics import extract_role_semantics


async def enrich_one(v: dict, run_id: str | None, rps_delay: float) -> None:
    text = f"{v.get('role_title','')}\n{v.get('description','')}"
    loc = await classify_location(
        text, run_id=run_id, vacancy_id=str(v.get("id"))
    )
    role = await extract_role_semantics(
        text, run_id=run_id, vacancy_id=str(v.get("id"))
    )
    cli = get_supabase()
    if cli is None:
        return
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
    q = (
        cli.table("vacancies")
        .select("id, role_title, description, status")
        .eq("status", "New")
        .is_("enrichment_at", "null")
        .limit(args.batch)
    )
    if profile_id:
        q = q.eq("profile_id", profile_id)
    res = q.execute()
    rows = getattr(res, "data", None) or []
    for v in rows:
        await enrich_one(v, args.run_id, args.rps)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=20)
    p.add_argument("--rps", type=float, default=0.2)
    p.add_argument("--run_id", default=None)
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
