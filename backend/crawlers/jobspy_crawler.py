from __future__ import annotations

import os

from backend.models.raw import RawVacancy


def fetch_jobspy_tier4(keywords: list[str], results_wanted: int = 25) -> list[RawVacancy]:
    """JobSpy (опционально, требует `pip install python-jobspy` и Python 3.10+)."""
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return []

    term = " OR ".join(f'"{k}"' for k in keywords[:5])
    base_sites = ["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"]
    extra = [s.strip() for s in (os.getenv("JOBSPY_SITES") or "").split(",") if s.strip()]
    sites = list(dict.fromkeys(base_sites + extra))
    jobs = scrape_jobs(
        site_name=sites,
        search_term=term,
        location="Europe",
        results_wanted=results_wanted,
        hours_old=120,
    )
    out: list[RawVacancy] = []
    if jobs is None or len(jobs) == 0:
        return out
    for _, row in jobs.iterrows():
        out.append(
            RawVacancy(
                title=str(row.get("title", "")),
                company=str(row.get("company", "")),
                description=str(row.get("description", ""))[:50000],
                location=str(row.get("location", "")),
                posted_at=None,
                url=str(row.get("job_url", "")),
                source="jobspy",
                tier="4",
                ats_type="jobspy",
            )
        )
    try:
        from backend.crawlers.wellfound import fetch_wellfound_jobspy

        extra_wf = fetch_wellfound_jobspy(keywords, results_wanted=min(12, results_wanted))
        seen = {x.url for x in out}
        for rv in extra_wf:
            if rv.url and rv.url not in seen:
                seen.add(rv.url)
                out.append(rv)
    except Exception:
        pass
    return out
