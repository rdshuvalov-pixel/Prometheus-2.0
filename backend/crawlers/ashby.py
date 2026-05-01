from __future__ import annotations

import re
from datetime import datetime
from html import unescape

import httpx

from backend.models.raw import RawVacancy


def ashby_org_slug(url: str) -> str | None:
    m = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)", url, re.I)
    return m.group(1) if m else None


def _strip_html(desc: str) -> str:
    if "<" not in desc:
        return desc
    return re.sub(r"<[^>]+>", " ", unescape(desc))


async def fetch_ashby_board(org_slug: str, company_name: str, tier: str) -> list[RawVacancy]:
    """Публичный Ashby Job Board API (док: developer job posting API — JSON по slug борда)."""
    out: list[RawVacancy] = []
    urls = [
        f"https://jobs.ashbyhq.com/posting-api/job-board/{org_slug}/jobs.json",
        f"https://api.ashbyhq.com/posting-api/job-board/{org_slug}",
    ]
    data: dict | None = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for api_url in urls:
            try:
                if api_url.endswith(".json"):
                    r = await client.get(api_url, params={"apiVersion": "1"})
                else:
                    r = await client.post(api_url, json={})
                if r.status_code >= 400:
                    continue
                data = r.json()
                break
            except Exception:
                continue
    if not data:
        return out

    jobs = data.get("jobs") or data.get("jobPostings") or []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        title = job.get("title") or job.get("name") or ""
        desc = (
            job.get("descriptionPlain")
            or job.get("descriptionHtml")
            or job.get("description")
            or ""
        )
        desc = _strip_html(str(desc))[:50000]
        loc = job.get("locationName") or job.get("location") or ""
        if isinstance(loc, dict):
            loc = loc.get("name", "") or str(loc.get("city", ""))
        job_url = job.get("jobUrl") or job.get("url") or f"https://jobs.ashbyhq.com/{org_slug}"
        posted = job.get("publishedAt") or job.get("published_at") or job.get("createdAt")
        dt = None
        if posted:
            try:
                dt = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
            except ValueError:
                dt = None
        if job.get("isListed") is False:
            continue
        out.append(
            RawVacancy(
                title=str(title)[:500],
                company=company_name,
                description=desc,
                location=str(loc),
                posted_at=dt,
                url=str(job_url),
                source="ashby",
                tier=tier,
                ats_type="ashby",
            )
        )
    return out
