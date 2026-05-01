"""python -m backend.pipeline.run_score"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase
from backend.llm.functions.explain import explain_fit
from backend.llm.functions.extract_scoring_features import (
    extract_scoring_features,
    extract_scoring_features_batch,
)
from backend.scoring.decision import vacancy_status_from_score
from backend.scoring.engine import compute_score, match_label


async def score_one(
    v: dict,
    overrides: dict | None,
    run_id: str | None,
    ext: object | None = None,
) -> None:
    text = f"{v.get('role_title','')}\n{v.get('description','')}"
    if ext is None:
        ext = await extract_scoring_features(text, run_id=run_id, vacancy_id=str(v.get("id")))
    feats = ext.model_dump()
    score, group_a, breakdown = compute_score(feats, overrides)
    status, reject_reason = vacancy_status_from_score(score, group_a)

    why = None
    rsks = None
    if score >= 50 and group_a:
        exp = await explain_fit(text, run_id=run_id, vacancy_id=str(v.get("id")))
        why = exp.why_kept
        rsks = exp.risks

    cli = get_supabase()
    if cli is None:
        return

    match_status = match_label(score)
    payload = {
        "score": score,
        "match_status": match_status,
        "score_breakdown": breakdown,
        "status": status,
        "reject_reason": reject_reason,
        "why_kept": why,
        "risks": rsks,
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }
    cli.table("vacancies").update(payload).eq("id", v["id"]).execute()


async def main_async(args: argparse.Namespace) -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Set OPENROUTER_API_KEY")
        return
    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    overrides = profile.scoring_overrides
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None:
        return
    q = (
        cli.table("vacancies")
        .select("id, role_title, description, status")
        .eq("status", "New")
        .not_.is_("enrichment_at", "null")
        .is_("score", "null")
        .limit(args.batch)
    )
    if profile_id:
        q = q.eq("profile_id", profile_id)
    res = q.execute()
    rows = getattr(res, "data", None) or []

    if args.batch_mode and len(rows) > 1:
        chunk_size = 5
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            texts = [f"{v.get('role_title','')}\n{v.get('description','')}" for v in chunk]
            vids = [str(v.get("id")) for v in chunk]
            try:
                extracted = await extract_scoring_features_batch(
                    texts, run_id=args.run_id, vacancy_ids=vids
                )
            except ValueError:
                raise
            except Exception:
                for v in chunk:
                    await score_one(v, overrides, args.run_id, None)
                    await asyncio.sleep(0.3)
                continue
            for v, ext in zip(chunk, extracted, strict=True):
                await score_one(v, overrides, args.run_id, ext)
                await asyncio.sleep(0.2)
    else:
        for v in rows:
            await score_one(v, overrides, args.run_id, None)
            await asyncio.sleep(0.3)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=15)
    p.add_argument("--run_id", default=None)
    p.add_argument(
        "--batch-mode",
        action="store_true",
        help="Один LLM-вызов на 5 вакансий (extract batch)",
    )
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
