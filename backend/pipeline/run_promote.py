"""python -m backend.pipeline.run_promote

Переносит финальные записи из `vacancies_stage` в `vacancies`.
Берём stage со статусом `ScoredSelected` (и score >= threshold, если задано),
делаем upsert в `vacancies` по (profile_id, url), отмечаем `promoted_at` в stage.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=int, default=50, help="Минимальный score для промоута")
    p.add_argument("--batch", type=int, default=200, help="Сколько строк промоутить за запуск")
    p.add_argument("--run-id", dest="run_id", default=None)
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    q = (
        cli.table("vacancies_stage")
        .select(
            "id, profile_id, url, company, role_title, description, posted_at, fetched_at,"
            " company_normalized, role_title_normalized, score, score_breakdown, warnings, evidence, reject_reason"
        )
        .eq("profile_id", profile_id)
        .eq("status", "ScoredSelected")
        .gte("score", int(args.threshold))
        .is_("promoted_at", "null")
        .order("created_at", desc=False)
        .limit(max(1, int(args.batch)))
    )
    if args.run_id:
        q = q.eq("run_id", args.run_id)
    res = q.execute()
    rows = getattr(res, "data", None) or []
    if not rows:
        print(json.dumps({"promoted": 0}, ensure_ascii=False))
        return

    promoted = 0
    now = _utc_iso()
    for r in rows:
        sid = r.get("id")
        url = r.get("url")
        if not sid or not url:
            continue

        payload = {
            "profile_id": profile_id,
            "company": r.get("company") or "",
            "role_title": r.get("role_title") or "",
            "role_title_normalized": r.get("role_title_normalized") or "",
            "company_normalized": r.get("company_normalized") or "",
            "url": url,
            "description": r.get("description") or "",
            "status": "Scored",
            "score": r.get("score"),
            "score_breakdown": r.get("score_breakdown"),
            "warnings": r.get("warnings") or [],
            "evidence": r.get("evidence"),
            "reject_reason": None,
            "posted_at": r.get("posted_at"),
            "fetched_at": r.get("fetched_at") or now,
        }

        cli.table("vacancies").upsert(payload, on_conflict="profile_id,url").execute()
        # Try to fetch master id for bookkeeping in stage (TЗ step #6).
        master_id = None
        try:
            m = (
                cli.table("vacancies")
                .select("id")
                .eq("profile_id", profile_id)
                .eq("url", url)
                .single()
                .execute()
            )
            master_id = (getattr(m, "data", None) or {}).get("id")
        except Exception:
            master_id = None

        cli.table("vacancies_stage").update(
            {
                "status": "Promoted",
                "promoted_at": now,
                "master_table_id": master_id,
                "added_to_master_at": now,
                "pipeline_status": "Added to master",
                "updated_at": now,
            }
        ).eq("id", sid).execute()
        promoted += 1

    print(json.dumps({"promoted": promoted}, ensure_ascii=False))


if __name__ == "__main__":
    main()

