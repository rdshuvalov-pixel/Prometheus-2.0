"""CLI: python -m backend.pipeline.run_report --run-id <uuid>

Собирает сводку по `vacancies_stage` и пишет:
- merge_run_metrics(run_id, metrics)
- log_event(run_id, "run_report", metrics)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from backend.db.client import (
    apply_active_profile_id,
    get_active_profile,
    log_event,
    merge_run_metrics,
)


def _pick_run_id(cli, profile_id: str) -> str | None:
    res = (
        cli.table("vacancies_stage")
        .select("run_id")
        .eq("profile_id", profile_id)
        .neq("run_id", None)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    rid = rows[0].get("run_id") if rows else None
    return str(rid) if rid else None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", dest="run_id", default=None, help="UUID pipeline_runs (опционально)")
    p.add_argument("--profile-id", dest="profile_id", default=None, help="UUID профиля candidate_profiles")
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None

    cli = __import__("backend.db.client", fromlist=["get_supabase"]).get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    run_id = args.run_id or _pick_run_id(cli, profile_id)
    q = cli.table("vacancies_stage").select("status, reject_reason").eq("profile_id", profile_id)
    if run_id:
        q = q.eq("run_id", run_id)
    res = q.limit(5000).execute()
    rows = getattr(res, "data", None) or []

    by_status = Counter(str(r.get("status") or "unknown") for r in rows)
    by_reason = Counter(str(r.get("reject_reason") or "unknown") for r in rows if r.get("reject_reason"))
    top_reasons = [{"reason": k, "count": v} for k, v in by_reason.most_common(10)]

    metrics = {
        "stage_rows": len(rows),
        "stage_by_status": dict(by_status),
        "stage_top_reject_reasons": top_reasons,
    }

    if run_id:
        merge_run_metrics(run_id, metrics)
        log_event(run_id, "run_report", metrics)

    print(json.dumps({"run_id": run_id, **metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()

