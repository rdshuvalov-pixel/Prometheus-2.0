"""python -m backend.pipeline.run_dedup_master_stage

TЗ step #4: dedup stage vacancies against master table (`vacancies`).

Logic (aligned with existing dedup_check):
- fetch master rows for same profile and same company_normalized
- compare role titles fuzzily
- if duplicate: set pipeline_status='Dubl', duplicate_of_id, duplicate_reason
- else: pipeline_status='Ready for scoring'
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.debug_log import dbg
from backend.pipeline.dedup import dedup_check
from backend.pipeline.normalize.text import normalize_company


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_existing_company(cli, *, profile_id: str, company_normalized: str) -> list[dict]:
    res = (
        cli.table("vacancies")
        .select("id, company, role_title, posted_at")
        .eq("profile_id", profile_id)
        .eq("company_normalized", company_normalized)
        .execute()
    )
    return getattr(res, "data", None) or []


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=200)
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

    processed = 0
    dubl = 0
    ready = 0

    q = (
        cli.table("vacancies_stage")
        .select("id, company, company_normalized, role_title, normalized_title, url, platform, location_normalized, seniority, posted_at")
        .eq("profile_id", profile_id)
        .eq("status", "Staged")
        .is_("duplicate_of_id", "null")
        .neq("company_normalized", "")
        .order("created_at", desc=False)
        .limit(max(1, int(args.batch)))
    )
    if args.run_id:
        q = q.eq("run_id", args.run_id)
    res = q.execute()
    rows = getattr(res, "data", None) or []
    # region agent log
    dbg(
        hypothesis_id="H1",
        location="backend/pipeline/run_dedup_master_stage.py:query",
        message="selected_rows",
        data={"rows": len(rows), "batch": int(args.batch), "has_run_id_filter": bool(args.run_id)},
        run_id=args.run_id,
    )
    # endregion
    if not rows:
        if args.run_id:
            merge_run_metrics(args.run_id, {"stage_dedup_master_processed": 0, "stage_dedup_master_dubl": 0, "stage_dedup_master_ready": 0})
        print(json.dumps({"processed": 0, "dubl": 0, "ready": 0}, ensure_ascii=False))
        return

    now = _utc_iso()
    for v in rows:
        processed += 1
        sid = v.get("id")
        if not sid:
            continue
        cn = (v.get("company_normalized") or "").strip() or normalize_company(v.get("company") or "")
        existing = _fetch_existing_company(cli, profile_id=profile_id, company_normalized=cn)
        dm = dedup_check(
            company=v.get("company") or "",
            role_title=v.get("normalized_title") or v.get("role_title") or "",
            existing_rows=existing,
            posted_at=v.get("posted_at"),
        )
        # region agent log
        dbg(
            hypothesis_id="H6",
            location="backend/pipeline/run_dedup_master_stage.py:dedup_one",
            message="dedup_decision",
            data={
                "id": str(sid),
                "company_norm": cn,
                "existing_count": len(existing),
                "is_duplicate": bool(dm.is_duplicate),
                "existing_id": dm.existing_id,
                "is_reapply": bool(dm.is_reapply),
            },
            run_id=args.run_id,
        )
        # endregion
        if dm.is_duplicate and dm.existing_id:
            dubl += 1
            cli.table("vacancies_stage").update(
                {
                    "pipeline_status": "Dubl",
                    "duplicate_of_id": dm.existing_id,
                    "duplicate_reason": "company+title_match",
                    "updated_at": now,
                }
            ).eq("id", sid).execute()
        else:
            ready += 1
            cli.table("vacancies_stage").update({"pipeline_status": "Ready for scoring", "updated_at": now}).eq("id", sid).execute()

    if args.run_id:
        merge_run_metrics(
            args.run_id,
            {"stage_dedup_master_processed": processed, "stage_dedup_master_dubl": dubl, "stage_dedup_master_ready": ready},
        )
    print(json.dumps({"processed": processed, "dubl": dubl, "ready": ready}, ensure_ascii=False))


if __name__ == "__main__":
    main()

