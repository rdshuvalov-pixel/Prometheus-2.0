from __future__ import annotations

import re

import httpx

from backend.models.raw import RawVacancy


def breezy_slug(url: str) -> str | None:
    m = re.search(r"([a-z0-9-]+)\.breezy\.hr", url, re.I)
    return m.group(1) if m else None


async def fetch_breezy(slug: str, company_name: str, tier: str) -> list[RawVacancy]:
    api = f"https://{slug}.breezy.hr/json"
    out: list[RawVacancy] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(api)
        r.raise_for_status()
        data = r.json()
    for job in data.get("jobs") or []:
        out.append(
            RawVacancy(
                title=job.get("name", ""),
                company=company_name,
                description=str(job.get("description", ""))[:50000],
                location=(
                    str(job.get("location", {}).get("name", ""))
                    if isinstance(job.get("location"), dict)
                    else ""
                ),
                posted_at=None,
                url=job.get("url") or api,
                source="breezy",
                tier=tier,
                ats_type="breezy",
            )
        )
    return out
