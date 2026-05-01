"""Smoke test OpenRouter: python -m backend.llm.smoke"""

from __future__ import annotations

import asyncio
import os
import sys

from pydantic import BaseModel, Field

from backend.llm.gateway import chat_json


class SmokeOut(BaseModel):
    ok: bool = Field(...)
    message: str = Field(default="")


async def main() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print("SKIP: OPENROUTER_API_KEY не задан", file=sys.stderr)
        sys.exit(0)
    out = await chat_json(
        [
            {"role": "system", "content": "Reply with JSON only."},
            {
                "role": "user",
                "content": 'Return JSON: {"ok": true, "message": "prometheus-smoke"}',
            },
        ],
        SmokeOut,
        tier="cheap",
        function="smoke",
    )
    print(out.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
