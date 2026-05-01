"""Wellfound (AngelList) через JobSpy при наличии пакета и поддерживаемого site_name."""

from __future__ import annotations

from backend.models.raw import RawVacancy


def fetch_wellfound_jobspy(keywords: list[str], results_wanted: int = 15) -> list[RawVacancy]:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return []

    term = " ".join(keywords[:4]) or "product manager"
    try:
        jobs = scrape_jobs(
            site_name=["wellfound"],
            search_term=term,
            location="Remote",
            results_wanted=results_wanted,
            hours_old=168,
        )
    except Exception:
        return []
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
                source="wellfound",
                tier="4",
                ats_type="wellfound",
            )
        )
    return out


async def fetch_wellfound_placeholder(query: str) -> list[RawVacancy]:
    """Алиас для расширений Tier 4; query интерпретируем как список ключевых слов через split."""
    parts = [p for p in query.replace(",", " ").split() if p]
    return fetch_wellfound_jobspy(parts or ["product"])
