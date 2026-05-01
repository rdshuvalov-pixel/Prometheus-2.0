from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RawVacancy(BaseModel):
    title: str
    company: str
    description: str = ""
    location: str = ""
    posted_at: datetime | None = None
    url: str
    source: str = ""
    tier: str | None = None
    ats_type: str | None = None
    employment_type: str | None = None
    content_hash: str = ""
