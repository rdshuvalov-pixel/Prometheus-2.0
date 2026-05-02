"""Загрузка seeds/ruslan_profile.yaml в candidate_profiles."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid5

import yaml
from dotenv import load_dotenv

from backend.db.client import PROFILE_NAMESPACE

load_dotenv()

_REPO = Path(__file__).resolve().parents[2]
_SEED = _REPO / "seeds" / "ruslan_profile.yaml"


def main() -> None:
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("SKIP seed: нет SUPABASE_URL / SUPABASE_SERVICE_KEY — профиль только из YAML локально.")
        return

    data = yaml.safe_load(_SEED.read_text(encoding="utf-8"))
    cli = create_client(url, key)
    name = str(data.get("name", "default"))
    pid = str(uuid5(PROFILE_NAMESPACE, name))
    row = {
        "id": pid,
        "name": data.get("name"),
        "profession": data.get("profession"),
        "search_keywords": data.get("search_keywords") or [],
        "resume_md": data.get("resume_md", ""),
        "interview_md": data.get("interview_md", ""),
        "work_history_md": data.get("work_history_md", ""),
        "scoring_overrides": data.get("scoring_overrides"),
        "is_default": True,
    }
    try:
        cli.table("candidate_profiles").delete().eq("is_default", True).execute()
        cli.table("candidate_profiles").insert(row).execute()
    except Exception as e:
        err = str(e).lower()
        if "row-level security" in err or "42501" in str(e):
            print(
                "Ошибка RLS: в SUPABASE_SERVICE_KEY должен быть ключ service_role "
                "(Supabase → Settings → API → service_role secret), не anon. "
                "Или выполните db/repairs/ensure_default_profile.sql в SQL Editor."
            )
        raise
    print(f"Seeded profile {row['id']}")


if __name__ == "__main__":
    main()
