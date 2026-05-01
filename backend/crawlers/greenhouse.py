from __future__ import annotations

import re
from datetime import datetime

import httpx

from backend.models.raw import RawVacancy


def board_token_from_url(url: str) -> str | None:
    m = re.search(r"boards\.greenhouse\.io/([^/?#]+)", url, re.I)
    if m:
        return m.group(1)
    m = re.search(r"greenhouse\.io/embed/job_board\?for=([^&]+)", url, re.I)
    return m.group(1) if m else None


async def fetch_greenhouse(board: str, company_name: str, tier: str) -> list[RawVacancy]:
    api = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    out: list[RawVacancy] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(api)
        r.raise_for_status()
        data = r.json()
    jobs = data.get("jobs") or []
    for job in jobs:
        raw_ts = job.get("updated_at") or job.get("first_published")
        dt = None
        if raw_ts:
            try:
                dt = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
            except ValueError:
                dt = None
        loc = job.get("location", {}) or {}
        loc_name = loc.get("name") if isinstance(loc, dict) else str(loc)
        out.append(
            RawVacancy(
                title=job.get("title", ""),
                company=company_name,
                description=str(job.get("content", ""))[:50000],
                location=str(loc_name or ""),
                posted_at=dt,
                url=job.get("absolute_url") or "",
                source="greenhouse",
                tier=tier,
                ats_type="greenhouse",
            )
        )
    return out
