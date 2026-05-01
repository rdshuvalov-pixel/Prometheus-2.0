"""Landing.jobs / EU tech boards — общий JobSpy-просмотр с JOBSPY_SITES."""

from __future__ import annotations

from backend.crawlers.jobspy_crawler import fetch_jobspy_tier4
from backend.models.raw import RawVacancy


async def fetch_landing_jobs_placeholder(query: str) -> list[RawVacancy]:
    parts = [p for p in query.replace(",", " ").split() if p]
    return fetch_jobspy_tier4(parts or ["developer"], results_wanted=15)
