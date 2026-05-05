"""python -m backend.pipeline.run_score"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timedelta, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.llm.functions.explain import explain_fit
from backend.llm.functions.extract_scoring_features import (
    extract_scoring_features,
    extract_scoring_features_batch,
)
from backend.scoring.decision import vacancy_status_from_score
from backend.scoring.engine import compute_score, match_label


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


async def score_one(
    v: dict,
    overrides: dict | None,
    run_id: str | None,
    ext: object | None = None,
) -> None:
    desc = (v.get("description") or "").strip()
    if len(desc) < 100 and not v.get("evidence"):
        cli = get_supabase()
        if cli is None:
            return
        cli.table("vacancies").update(
            {"warnings": _merge_warnings(v.get("warnings"), "short_description")}
        ).eq("id", v["id"]).execute()
        return

    text = f"{v.get('role_title', '')}\n{v.get('description', '')}"
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
    since_iso = _since_start_iso(args.since)
    scored = 0
    while True:
        q = (
            cli.table("vacancies")
            .select("id, role_title, description, status, evidence, warnings, created_at")
            .eq("status", "New")
            .not_.is_("enrichment_at", "null")
            .is_("score", "null")
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
                merge_run_metrics(args.run_id, {"scored": scored})
            return

        to_score: list[dict] = []
        for v in rows:
            if len((v.get("description") or "").strip()) < 100 and not v.get("evidence"):
                await score_one(v, overrides, args.run_id, None)
                scored += 1
            else:
                to_score.append(v)
        rows = to_score

        if args.batch_mode and len(rows) > 1:
            chunk_size = args.chunk_size
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i : i + chunk_size]
                if not chunk:
                    continue
                texts = [f"{v.get('role_title', '')}\n{v.get('description', '')}" for v in chunk]
                vids = [str(v.get("id")) for v in chunk]
                try:
                    extracted = await extract_scoring_features_batch(texts, run_id=args.run_id, vacancy_ids=vids)
                except ValueError:
                    raise
                except Exception:
                    for v in chunk:
                        await score_one(v, overrides, args.run_id, None)
                        scored += 1
                        await asyncio.sleep(args.delay)
                    continue
                for v, ext in zip(chunk, extracted, strict=True):
                    await score_one(v, overrides, args.run_id, ext)
                    scored += 1
                    await asyncio.sleep(args.delay)
        else:
            for v in rows:
                await score_one(v, overrides, args.run_id, None)
                scored += 1
                await asyncio.sleep(args.delay)

        if not args.drain:
            if args.run_id:
                merge_run_metrics(args.run_id, {"scored": scored})
            return


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=15)
    p.add_argument("--run_id", default=None)
    p.add_argument("--drain", action="store_true", help="Process batches until queue is empty")
    p.add_argument(
        "--batch-mode",
        action="store_true",
        help="Один LLM-вызов на 5 вакансий (extract batch)",
    )
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=5)
    p.add_argument("--delay", type=float, default=0.25, help="Per-item delay in seconds")
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
