"""python -m backend.pipeline.run_check_status_stage

TЗ command: check_status
Returns counters for `vacancies_stage` readiness and progression.
"""

from __future__ import annotations

import argparse
import json

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase


def _count(cli, table: str, *, profile_id: str, filters: list[tuple[str, str, object]]) -> int:
    q = cli.table(table).select("id", count="exact").eq("profile_id", profile_id)
    for op, key, val in filters:
        if op == "eq":
            q = q.eq(key, val)
        elif op == "neq":
            q = q.neq(key, val)
        elif op == "is":
            q = q.is_(key, val)
        else:
            raise ValueError(op)
    res = q.execute()
    return int(getattr(res, "count", None) or 0)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    out = {
        "stage_total": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[]),
        "stage_without_full_text": _count(
            cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "status", "Staged"), ("is", "page_text_full", "null")]
        )
        + _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "status", "Staged"), ("eq", "page_text_full", "")]),
        "stage_enriched": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "pipeline_status", "Enriched")]),
        "stage_llm_normalized": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "pipeline_status", "Normalized")]),
        "stage_dubl": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "pipeline_status", "Dubl")]),
        "stage_ready_for_scoring": _count(
            cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "pipeline_status", "Ready for scoring")]
        ),
        "stage_score_gt_50": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "status", "ScoredSelected")]),
        "stage_ready_for_promote": _count(
            cli,
            "vacancies_stage",
            profile_id=profile_id,
            filters=[("eq", "status", "ScoredSelected"), ("is", "promoted_at", "null")],
        ),
        "stage_promoted": _count(cli, "vacancies_stage", profile_id=profile_id, filters=[("eq", "status", "Promoted")]),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

