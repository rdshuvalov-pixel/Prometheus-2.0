from __future__ import annotations

from pydantic import BaseModel, Field

from backend.llm.gateway import chat_json_with_fallback


class LetterOut(BaseModel):
    body: str = Field(..., description="Formal cover letter body")


SYSTEM = """Write a formal cover letter for Ruslan (Senior PM, EU remote). Use resume and interview notes.
Output JSON { "body": "..." } only."""


async def generate_formal(
    resume_md: str,
    interview_md: str,
    work_history_md: str,
    vacancy_block: str,
    *,
    run_id: str | None = None,
    vacancy_id: str | None = None,
) -> str:
    user = (
        f"Resume:\n{resume_md[:8000]}\n\nInterview notes:\n{interview_md[:4000]}\n\n"
        f"Work history:\n{work_history_md[:4000]}\n\nVacancy:\n{vacancy_block[:6000]}"
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
    out = await chat_json_with_fallback(
        messages,
        LetterOut,
        tier="strong",
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="cover_formal",
    )
    return out.body
