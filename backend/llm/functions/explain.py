from __future__ import annotations

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.schemas import ExplainOut

SYSTEM = """Summarize why this job fits Ruslan (senior PM, B2B SaaS/FinTech, EU remote).
JSON only: why_kept[], risks[], evidence[]."""


async def explain_fit(text: str, *, run_id: str | None = None, vacancy_id: str | None = None) -> ExplainOut:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text[:12000]},
    ]
    return await chat_json_with_fallback(
        messages,
        ExplainOut,
        tier="strong",
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="explain_fit",
    )
