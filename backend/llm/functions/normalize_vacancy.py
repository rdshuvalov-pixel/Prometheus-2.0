from __future__ import annotations

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.schemas import NormalizeVacancy

SYSTEM = """You normalize a job vacancy into structured fields for downstream deduplication and scoring.

Rules:
- Use only evidence from the provided inputs.
- If a field is not present, return null (or empty list for list fields).
- Do NOT guess.
- Keep strings short and canonical where possible.
- normalization_confidence: 0..1.
- JSON only.
"""


async def normalize_vacancy(
    *,
    job_title: str,
    company_name: str,
    job_url: str,
    job_description: str,
    page_text_full: str,
    location_raw: str,
    platform: str,
    run_id: str | None = None,
    vacancy_id: str | None = None,
) -> NormalizeVacancy:
    user = "\n".join(
        [
            f"job_title: {job_title}".strip(),
            f"company_name: {company_name}".strip(),
            f"job_url: {job_url}".strip(),
            f"platform: {platform}".strip(),
            f"location_raw: {location_raw}".strip(),
            "--- job_description ---",
            (job_description or "")[:14000],
            "--- page_text_full ---",
            (page_text_full or "")[:20000],
        ]
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user[:60000]},
    ]
    return await chat_json_with_fallback(
        messages,
        NormalizeVacancy,
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="normalize_vacancy",
    )

