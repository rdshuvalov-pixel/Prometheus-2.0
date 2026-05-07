"""python -m backend.pipeline.run_score_stage

Scoring + filters step for `vacancies_stage`.
Input: rows with status=DedupKept and score is null.
Output: score + score_breakdown + status (ScoredSelected/ScoredRejected) + reject_reason.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.llm.functions.extract_scoring_features import extract_scoring_features_batch
from backend.scoring.decision import vacancy_status_from_score
from backend.scoring.engine import compute_score


def _merge_warnings(existing: object, *codes: str) -> list[str]:
    cur = list(existing) if isinstance(existing, list) else []
    out = [*cur]
    for c in codes:
        if c not in out:
            out.append(c)
    return out


def _stage_status_from_vacancy_status(vac_status: str) -> str:
    return "ScoredSelected" if vac_status == "Scored" else "ScoredRejected"


async def main_async(args: argparse.Namespace) -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Set OPENROUTER_API_KEY")
        return

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    overrides = profile.scoring_overrides
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        return

    scored = 0
    selected = 0
    rejected = 0
    while True:
        q = (
            cli.table("vacancies_stage")
            .select("id, role_title, description, evidence, warnings, created_at")
            .eq("profile_id", profile_id)
            .eq("status", "DedupKept")
            .is_("score", "null")
            .order("created_at", desc=False)
            .limit(args.batch)
        )
        if args.run_id:
            q = q.eq("run_id", args.run_id)
        res = q.execute()
        rows = getattr(res, "data", None) or []
        if not rows:
            if args.run_id:
                merge_run_metrics(args.run_id, {"stage_scored": scored, "stage_selected": selected, "stage_rejected": rejected})
            return

        # short description guard: mark rejected but keep pipeline moving
        to_score: list[dict] = []
        for v in rows:
            desc = (v.get("description") or "").strip()
            if len(desc) < 100 and not v.get("evidence"):
                cli.table("vacancies_stage").update(
                    {
                        "warnings": _merge_warnings(v.get("warnings"), "short_description"),
                        "status": "ScoredRejected",
                        "reject_reason": "short_description",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).eq("id", v["id"]).execute()
                scored += 1
                rejected += 1
            else:
                to_score.append(v)
        rows = to_score

        if rows:
            chunk_size = args.chunk_size
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i : i + chunk_size]
                texts = [f"{v.get('role_title', '')}\n{v.get('description', '')}" for v in chunk]
                vids = [str(v.get("id")) for v in chunk]
                extracted = await extract_scoring_features_batch(texts, run_id=args.run_id, vacancy_ids=vids)
                for v, ext in zip(chunk, extracted, strict=True):
                    feats = ext.model_dump()
                    score, group_a, breakdown = compute_score(feats, overrides)
                    vac_status, reject_reason = vacancy_status_from_score(score, group_a)
                    stage_status = _stage_status_from_vacancy_status(vac_status)
                    payload = {
                        "score": score,
                        "score_breakdown": breakdown,
                        "status": stage_status,
                        "reject_reason": reject_reason,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    cli.table("vacancies_stage").update(payload).eq("id", v["id"]).execute()
                    scored += 1
                    if stage_status == "ScoredSelected":
                        selected += 1
                    else:
                        rejected += 1
                    await asyncio.sleep(args.delay)

        if not args.drain:
            if args.run_id:
                merge_run_metrics(args.run_id, {"stage_scored": scored, "stage_selected": selected, "stage_rejected": rejected})
            return


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=50)
    p.add_argument("--run-id", dest="run_id", default=None)
    p.add_argument("--drain", action="store_true")
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=5)
    p.add_argument("--delay", type=float, default=0.2)
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

