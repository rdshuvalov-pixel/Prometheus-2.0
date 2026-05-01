from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import dateparser


def parse_posted_at(raw: str | None, now: datetime | None = None) -> datetime | None:
    if not raw:
        return None
    now = now or datetime.now(timezone.utc)
    settings = {"RETURN_AS_TIMEZONE_AWARE": True}
    dt = dateparser.parse(raw, settings=settings)
    if dt is None:
        return None
    return dt


def is_stale(posted_at: datetime | None, max_days: int = 5, now: datetime | None = None) -> bool:
    """True если вакансия старше max_days."""
    if posted_at is None:
        return False
    now = now or datetime.now(timezone.utc)
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    return posted_at < now - timedelta(days=max_days)
