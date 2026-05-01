from __future__ import annotations

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.schemas import LocationClassify

SYSTEM = """You classify job location/work format for EU/remote hiring.
Return JSON only with keys: work_format (remote|hybrid|office|unknown), eu_compatible (bool),
confidence (0-1), evidence (array of short quotes from text)."""


async def classify_location(text: str, *, run_id: str | None = None, vacancy_id: str | None = None) -> LocationClassify:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text[:12000]},
    ]
    return await chat_json_with_fallback(
        messages,
        LocationClassify,
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="classify_location",
    )
