from __future__ import annotations

from pydantic import BaseModel, Field

from backend.llm.gateway import chat_json_with_fallback


class ShortMsg(BaseModel):
    body: str = Field(..., description="Short LinkedIn / recruiter message, under 150 words")


SYSTEM = """Write a short informal outreach message. JSON { "body": "..." } only."""


async def generate_informal(
    resume_md: str,
    vacancy_block: str,
    *,
    run_id: str | None = None,
    vacancy_id: str | None = None,
) -> str:
    user = f"""Resume summary:\n{resume_md[:4000]}\n\nVacancy:\n{vacancy_block[:4000]}"""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    out = await chat_json_with_fallback(
        messages,
        ShortMsg,
        tier="strong",
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="cover_informal",
    )
    return out.body
