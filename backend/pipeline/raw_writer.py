from __future__ import annotations

import hashlib
import json

from backend.db.client import get_supabase
from backend.models.raw import RawVacancy


def content_hash(rv: RawVacancy) -> str:
    payload = f"{rv.url}|{rv.title}|{rv.company}"
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def persist_raw(rv: RawVacancy) -> bool:
    """Вставить raw_vacancies если нет дубликата по hash. Возвращает True если вставлено."""
    cli = get_supabase()
    if cli is None:
        return False
    h = content_hash(rv)
    row = {
        "payload": json.loads(rv.model_dump_json()),
        "source": rv.source,
        "content_hash": h,
    }
    try:
        cli.table("raw_vacancies").insert(row).execute()
        return True
    except Exception:
        return False
