from __future__ import annotations

import re

import httpx

from backend.models.raw import RawVacancy


def short_from_url(url: str) -> str | None:
    m = re.search(r"apply\.workable\.com/([^/?#]+)", url, re.I)
    return m.group(1) if m else None


async def fetch_workable(short: str, company_name: str, tier: str) -> list[RawVacancy]:
    api = f"https://apply.workable.com/api/v3/accounts/{short}/jobs"
    out: list[RawVacancy] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(api)
        r.raise_for_status()
        data = r.json()
    for job in data.get("results") or []:
        out.append(
            RawVacancy(
                title=job.get("title", ""),
                company=company_name,
                description=str(job.get("description", ""))[:50000],
                location=", ".join(
                    c.get("city", "") for c in (job.get("locations") or []) if isinstance(c, dict)
                ),
                posted_at=None,
                url=job.get("url") or api,
                source="workable",
                tier=tier,
                ats_type="workable",
            )
        )
    return out
