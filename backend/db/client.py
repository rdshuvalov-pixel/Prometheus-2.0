from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

import yaml
from dotenv import load_dotenv

from backend.models.profile import CandidateProfile

PROFILE_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

load_dotenv()

_SUPABASE_CLIENT: Any = None
_REPO_ROOT = Path(__file__).resolve().parents[2]


def apply_active_profile_id(profile_id: str | None) -> None:
    """Подставить активный профиль для CLI пайплайна (совпадает с cookie UI)."""
    if profile_id:
        os.environ["ACTIVE_PROFILE_ID"] = profile_id


def get_supabase() -> Any:
    """Lazy singleton Supabase client (service role)."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    from supabase import create_client

    _SUPABASE_CLIENT = create_client(url, key)
    return _SUPABASE_CLIENT


def load_profile_from_yaml(path: Path | None = None) -> CandidateProfile:
    p = path or _REPO_ROOT / "seeds" / "ruslan_profile.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    name = data.get("name", "default")
    pid = uuid5(PROFILE_NAMESPACE, str(name))
    return CandidateProfile.model_validate(
        {
            "id": pid,
            "name": name,
            "profession": data.get("profession", ""),
            "search_keywords": data.get("search_keywords") or [],
            "resume_md": data.get("resume_md", ""),
            "interview_md": data.get("interview_md", ""),
            "work_history_md": data.get("work_history_md", ""),
            "scoring_overrides": data.get("scoring_overrides"),
            "is_default": True,
        }
    )


def get_active_profile() -> CandidateProfile:
    """Активный профиль: ACTIVE_PROFILE_ID → Supabase → дефолтный профиль → YAML."""
    cli = get_supabase()
    override = os.getenv("ACTIVE_PROFILE_ID")
    if cli is not None and override:
        res = cli.table("candidate_profiles").select("*").eq("id", override).limit(1).execute()
        rows_ov = getattr(res, "data", None) or []
        if rows_ov:
            r = rows_ov[0]
            return CandidateProfile(
                id=UUID(r["id"]) if r.get("id") else None,
                name=r.get("name") or "",
                profession=r.get("profession") or "",
                search_keywords=list(r.get("search_keywords") or []),
                resume_md=r.get("resume_md") or "",
                interview_md=r.get("interview_md") or "",
                work_history_md=r.get("work_history_md") or "",
                scoring_overrides=r.get("scoring_overrides"),
                is_default=bool(r.get("is_default")),
            )
    if cli is None:
        return load_profile_from_yaml()
    res = (
        cli.table("candidate_profiles")
        .select("*")
        .eq("is_default", True)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        return load_profile_from_yaml()
    r = rows[0]
    return CandidateProfile(
        id=UUID(r["id"]) if r.get("id") else None,
        name=r.get("name") or "",
        profession=r.get("profession") or "",
        search_keywords=list(r.get("search_keywords") or []),
        resume_md=r.get("resume_md") or "",
        interview_md=r.get("interview_md") or "",
        work_history_md=r.get("work_history_md") or "",
        scoring_overrides=r.get("scoring_overrides"),
        is_default=bool(r.get("is_default")),
    )


def insert_run(profile_id: str | UUID | None = None) -> str | None:
    cli = get_supabase()
    if cli is None:
        return None
    row = {
        "profile_id": str(profile_id) if profile_id else None,
        "status": "running",
        "metrics": {},
    }
    res = cli.table("pipeline_runs").insert(row).execute()
    data = getattr(res, "data", None) or []
    if data:
        return str(data[0]["id"])
    return None


def finish_run(
    run_id: str,
    status: str,
    metrics: dict[str, Any],
) -> None:
    cli = get_supabase()
    if cli is None:
        return
    finished = datetime.now(timezone.utc).isoformat()
    try:
        cur = cli.table("pipeline_runs").select("metrics").eq("id", run_id).limit(1).execute()
        rows = getattr(cur, "data", None) or []
        base = rows[0].get("metrics") if rows else {}
        if not isinstance(base, dict):
            base = {}
    except Exception:
        base = {}
    merged = {**base, **metrics}
    cli.table("pipeline_runs").update(
        {"finished_at": finished, "status": status, "metrics": merged}
    ).eq("id", run_id).execute()


def merge_run_metrics(run_id: str, patch: dict[str, Any]) -> None:
    """Merge metrics into pipeline_runs.metrics (best-effort)."""
    cli = get_supabase()
    if cli is None:
        return
    try:
        cur = cli.table("pipeline_runs").select("metrics").eq("id", run_id).limit(1).execute()
        rows = getattr(cur, "data", None) or []
        base = rows[0].get("metrics") if rows else {}
        if not isinstance(base, dict):
            base = {}
    except Exception:
        base = {}
    merged = {**base, **patch}
    cli.table("pipeline_runs").update({"metrics": merged}).eq("id", run_id).execute()


def log_event(
    run_id: str | None,
    type_: str,
    payload: dict[str, Any],
    level: str = "info",
) -> None:
    cli = get_supabase()
    if cli is None:
        return
    cli.table("pipeline_events").insert(
        {
            "run_id": run_id,
            "type": type_,
            "payload": payload,
            "level": level,
        }
    ).execute()
