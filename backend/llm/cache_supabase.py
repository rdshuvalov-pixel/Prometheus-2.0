"""Кеш LLM-ответов по url + content_hash + function_name."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.db.client import get_supabase


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


def cache_get(url: str, content_hash: str, function_name: str) -> dict[str, Any] | None:
    cli = get_supabase()
    if cli is None:
        return None
    res = (
        cli.table("llm_response_cache")
        .select("response_json")
        .eq("url", url)
        .eq("content_hash", content_hash)
        .eq("function_name", function_name)
        .limit(1)
        .execute()
    )
    rows = getattr(res, "data", None) or []
    if not rows:
        return None
    return rows[0]["response_json"]


def cache_set(url: str, content_hash: str, function_name: str, response_json: dict[str, Any]) -> None:
    cli = get_supabase()
    if cli is None:
        return
    cli.table("llm_response_cache").upsert(
        {
            "url": url,
            "content_hash": content_hash,
            "function_name": function_name,
            "response_json": response_json,
        },
        on_conflict="url,content_hash,function_name",
    ).execute()
