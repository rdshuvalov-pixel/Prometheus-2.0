"""Welcome to the Jungle: без отдельного API — добираем EU через JobSpy (Indeed/Glassdoor)."""

from __future__ import annotations

from backend.crawlers.jobspy_crawler import fetch_jobspy_tier4
from backend.models.raw import RawVacancy


async def fetch_wttj_placeholder(query: str) -> list[RawVacancy]:
    parts = [p for p in query.replace(",", " ").split() if p]
    return fetch_jobspy_tier4(parts or ["product manager"], results_wanted=15)
