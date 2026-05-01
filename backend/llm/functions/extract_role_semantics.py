from __future__ import annotations

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.schemas import RoleSemantics

SYSTEM = """Determine if role is true Product Management vs project/marketing.
Domains: ai, fintech, saas, ecommerce, other. JSON only."""


async def extract_role_semantics(text: str, *, run_id: str | None = None, vacancy_id: str | None = None) -> RoleSemantics:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text[:12000]},
    ]
    return await chat_json_with_fallback(
        messages,
        RoleSemantics,
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="extract_role_semantics",
    )
