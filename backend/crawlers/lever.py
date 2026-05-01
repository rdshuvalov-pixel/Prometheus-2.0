from __future__ import annotations

import re
from datetime import datetime

import httpx

from backend.models.raw import RawVacancy


def slug_from_url(url: str) -> str | None:
    m = re.search(r"jobs\.lever\.co/([^/?#]+)", url, re.I)
    return m.group(1) if m else None


async def fetch_lever_board(board_slug: str, company_name: str, tier: str) -> list[RawVacancy]:
    api = f"https://api.lever.co/v0/postings/{board_slug}?mode=json"
    out: list[RawVacancy] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(api)
        r.raise_for_status()
        data = r.json()
    for job in data:
        posted = job.get("createdAt") or job.get("timestamp")
        dt = None
        if posted:
            try:
                dt = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
            except ValueError:
                dt = None
        lists = job.get("lists") or []
        desc = job.get("description") or ""
        if not desc and lists:
            desc = (lists[0] or {}).get("text", "") if isinstance(lists[0], dict) else ""
        if isinstance(desc, list):
            desc = "\n".join(str(x) for x in desc)
        out.append(
            RawVacancy(
                title=job.get("text", ""),
                company=company_name,
                description=str(desc)[:50000],
                location=(job.get("categories", {}) or {}).get("location", "") or "",
                posted_at=dt,
                url=job.get("hostedUrl") or job.get("applyUrl") or api,
                source="lever",
                tier=tier,
                ats_type="lever",
            )
        )
    return out
