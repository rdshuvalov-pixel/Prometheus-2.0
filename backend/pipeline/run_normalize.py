"""CLI: python -m backend.pipeline.run_normalize --batch 200

Заполняет в `vacancies_stage` поля:
- company_normalized
- role_title_normalized
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile
from backend.pipeline.normalize.text import normalize_company, normalize_title


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=200, help="Сколько строк обработать за запуск")
    p.add_argument("--profile-id", dest="profile_id", default=None, help="UUID профиля candidate_profiles")
    args = p.parse_args()

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None

    cli = __import__("backend.db.client", fromlist=["get_supabase"]).get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    res = (
        cli.table("vacancies_stage")
        .select("id, company, role_title, company_normalized, role_title_normalized")
        .eq("profile_id", profile_id)
        .or_("company_normalized.eq.,role_title_normalized.eq.")
        .order("created_at", desc=True)
        .limit(max(1, int(args.batch)))
        .execute()
    )
    rows = getattr(res, "data", None) or []

    updated = 0
    for r in rows:
        cid = r.get("id")
        if not cid:
            continue
        cn = (r.get("company_normalized") or "").strip() or normalize_company(r.get("company") or "")
        tn = (r.get("role_title_normalized") or "").strip() or normalize_title(r.get("role_title") or "")
        cli.table("vacancies_stage").update(
            {"company_normalized": cn, "role_title_normalized": tn, "updated_at": _utc_iso()}
        ).eq("id", cid).execute()
        updated += 1

    print(json.dumps({"updated": updated, "batch": int(args.batch)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

