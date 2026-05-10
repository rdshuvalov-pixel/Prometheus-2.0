from __future__ import annotations

import dataclasses

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.normalize_enums import coerce_normalize_enums
from backend.llm.schemas import NormalizeVacancy

# Bump when SYSTEM/user rules change (docs/llm_prompt.md §15).
JOB_NORMALIZATION_PROMPT_VERSION = "job_normalization_v1"

# docs/llm_prompt.md §4–5: compact body for one vacancy.
_MAX_JOB_BODY_CHARS = 16000

SYSTEM = """You are a job-posting normalization engine.

Your task is to extract structured fields from a job posting.

Return only valid JSON. Do not include markdown, explanations, or comments.

Use null when a value is not clearly present or cannot be reasonably inferred.

Do not invent salary, location, seniority, remote status, or employment type.

Prefer explicit metadata fields over body text when they conflict.

Output must match the schema requested in the user message (JSON object only)."""


USER_RULES = """Extract normalized job fields from the following job posting.

Rules:
- normalized_title: clean role title without company, location, remote/hybrid, or employment type.
- seniority: one of Intern, Junior, Middle, Senior, Lead, Principal, Head, Director, VP, C-level, Unknown.
- function: one of Product Management, Product Marketing, Growth, Data, Engineering, Design, Operations, Sales, Marketing, Customer Success, Other, Unknown.
- work_format: one of Remote, Hybrid, Onsite, Flexible, Unknown.
- technical_depth: one of Low, Medium, High, Unknown.
- b2b_or_b2c: one of B2B, B2C, B2B2C, Marketplace, Internal, Unknown.
- salary_min, salary_max, salary_currency must be null unless explicit compensation exists.
- remote_allowed and hybrid_allowed must be null unless explicitly stated or strongly implied.
- english_required should be true if English is explicitly required or the posting is entirely in English for an international role.
- requirements and responsibilities must be short, deduplicated lists.
- red_flags: possible mismatch signals for a senior product / growth / AI / fintech-oriented candidate.
- positive_signals: attractive or relevant signals.
- normalization_confidence: number from 0 to 1.

Return JSON with exactly these keys (arrays may be empty):
normalized_title, seniority, function, domain, industry, employment_type, work_format,
location_normalized, country, remote_allowed, hybrid_allowed, relocation_required,
salary_min, salary_max, salary_currency, english_required, product_type, b2b_or_b2c,
ai_related, fintech_related, growth_related, monetization_related, platform_related,
technical_depth, management_scope, must_have_requirements, nice_to_have_requirements,
responsibilities, red_flags, positive_signals, normalization_confidence"""


def build_normalize_job_body(
    *,
    job_title: str,
    company_name: str,
    job_url: str,
    platform: str,
    location_raw: str,
    job_description: str,
    page_text_full: str,
    max_chars: int = _MAX_JOB_BODY_CHARS,
) -> tuple[str, int]:
    """Prioritize job_description, then page_text_full; cap total size (docs/llm_prompt.md §4–5)."""
    sep = "\n--- job_description ---\n"
    sep2 = "\n--- page_text_full ---\n"
    header = "\n".join(
        [
            f"job_title: {job_title.strip()}",
            f"company_name: {company_name.strip()}",
            f"job_url: {job_url.strip()}",
            f"platform: {platform.strip()}",
            f"location_raw: {location_raw.strip()}",
        ]
    )
    overhead = len(header) + len(sep) + len(sep2)
    budget = max(0, max_chars - overhead)
    desc = (job_description or "").strip()
    page = (page_text_full or "").strip()
    # Prefer description up to 70% of budget, rest for page
    desc_budget = min(len(desc), int(budget * 0.7))
    desc_part = desc[:desc_budget]
    rest = budget - len(desc_part)
    page_part = page[: rest]
    body = f"{header}{sep}{desc_part}{sep2}{page_part}"
    if len(body) > max_chars:
        body = body[:max_chars]
    return body, len(body)


@dataclasses.dataclass(frozen=True)
class NormalizeVacancyOutcome:
    payload: NormalizeVacancy
    llm_model: str
    input_char_count: int
    prompt_version: str
    enum_coerced: bool


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
) -> NormalizeVacancyOutcome:
    body, _body_len = build_normalize_job_body(
        job_title=job_title,
        company_name=company_name,
        job_url=job_url,
        platform=platform,
        location_raw=location_raw,
        job_description=job_description,
        page_text_full=page_text_full,
    )
    user = f"{USER_RULES}\n\n---\n\nJob posting:\n\n{body}"
    input_cc = len(user)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    out_model: list[str] = []
    raw = await chat_json_with_fallback(
        messages,
        NormalizeVacancy,
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="normalize_vacancy",
        temperature=0.0,
        out_model=out_model,
    )
    fixed, coerced = coerce_normalize_enums(raw)
    llm_model = out_model[0] if out_model else ""
    return NormalizeVacancyOutcome(
        payload=fixed,
        llm_model=llm_model,
        input_char_count=input_cc,
        prompt_version=JOB_NORMALIZATION_PROMPT_VERSION,
        enum_coerced=coerced,
    )
