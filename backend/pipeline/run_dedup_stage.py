"""CLI: python -m backend.pipeline.run_dedup_stage --batch 500

Дедуп внутри `vacancies_stage` по `(profile_id, dedup_key)` где:
dedup_key = company_normalized + "|" + role_title_normalized.

Выбираем "best" запись по posted_at desc (fallback: created_at desc) и помечаем:
- best: status = DedupKept
- остальные: status = DedupDropped
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=500, help="Сколько строк stage обработать за запуск")
    p.add_argument("--profile-id", dest="profile_id", default=None, help="UUID профиля candidate_profiles")
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None

    cli = __import__("backend.db.client", fromlist=["get_supabase"]).get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    # Take only staged rows with normalized keys present.
    res = (
        cli.table("vacancies_stage")
        .select("id, company_normalized, role_title_normalized, posted_at, created_at")
        .eq("profile_id", profile_id)
        .eq("status", "Staged")
        .neq("company_normalized", "")
        .neq("role_title_normalized", "")
        .order("created_at", desc=True)
        .limit(max(1, int(args.batch)))
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        print(json.dumps({"groups": 0, "kept": 0, "dropped": 0}, ensure_ascii=False))
        return

    groups: dict[str, list[dict]] = {}
    for r in rows:
        key = f"{r.get('company_normalized') or ''}|{r.get('role_title_normalized') or ''}"
        groups.setdefault(key, []).append(r)

    kept = 0
    dropped = 0
    for key, g in groups.items():
        if not key.strip("|"):
            continue

        def _sort_key(x: dict) -> tuple:
            # posted_at can be null; keep it last
            posted = x.get("posted_at")
            created = x.get("created_at")
            return (posted is not None, posted or "", created or "")

        g_sorted = sorted(g, key=_sort_key, reverse=True)
        best = g_sorted[0]
        best_id = best.get("id")
        if not best_id:
            continue

        cli.table("vacancies_stage").update(
            {"dedup_key": key, "dedup_status": "keep", "status": "DedupKept", "updated_at": _utc_iso()}
        ).eq("id", best_id).execute()
        kept += 1

        for r in g_sorted[1:]:
            rid = r.get("id")
            if not rid:
                continue
            cli.table("vacancies_stage").update(
                {"dedup_key": key, "dedup_status": "drop", "status": "DedupDropped", "updated_at": _utc_iso()}
            ).eq("id", rid).execute()
            dropped += 1

    print(json.dumps({"groups": len(groups), "kept": kept, "dropped": dropped}, ensure_ascii=False))


if __name__ == "__main__":
    main()

