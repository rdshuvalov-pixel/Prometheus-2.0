"""python -m backend.pipeline.run_write"""

from __future__ import annotations

import argparse
import asyncio
import os

from backend.db.client import apply_active_profile_id, get_supabase
from backend.writer.formal import generate_formal
from backend.writer.informal import generate_informal
from backend.writer.profile_loader import load_profile_for_writing


async def write_one(v: dict, profile, run_id: str | None) -> None:
    block = f"{v.get('role_title','')}\n{v.get('company','')}\n{v.get('description','')}"
    formal_b, informal_b = await asyncio.gather(
        generate_formal(
            profile.resume_md,
            profile.interview_md,
            profile.work_history_md,
            block,
            run_id=run_id,
            vacancy_id=str(v.get("id")),
        ),
        generate_informal(
            profile.resume_md,
            block,
            run_id=run_id,
            vacancy_id=str(v.get("id")),
        ),
    )
    cli = get_supabase()
    if cli is None:
        return
    vid = str(v["id"])
    cli.table("cover_letters").upsert(
        {"vacancy_id": vid, "kind": "formal", "body": formal_b, "model": "openrouter"},
        on_conflict="vacancy_id,kind",
    ).execute()
    cli.table("cover_letters").upsert(
        {"vacancy_id": vid, "kind": "informal", "body": informal_b, "model": "openrouter"},
        on_conflict="vacancy_id,kind",
    ).execute()


async def main_async(args: argparse.Namespace) -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Set OPENROUTER_API_KEY")
        return
    apply_active_profile_id(args.profile_id)
    profile = load_profile_for_writing()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None:
        return
    q = (
        cli.table("vacancies")
        .select("id, role_title, description, company, status, score")
        .eq("status", "Scored")
        .gte("score", 50)
        .limit(args.batch)
    )
    if profile_id:
        q = q.eq("profile_id", profile_id)
    res = q.execute()
    rows = getattr(res, "data", None) or []
    for v in rows:
        await write_one(v, profile, args.run_id)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--run_id", default=None)
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
