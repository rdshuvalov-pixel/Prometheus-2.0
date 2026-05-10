from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, TypeVar

import httpx
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.db.client import get_supabase, log_event
from backend.llm.cache_supabase import cache_get, cache_set, compute_content_hash
from backend.llm.schemas import ExtractScoring

load_dotenv()

T = TypeVar("T", bound=BaseModel)
_MODELS_PATH = Path(__file__).resolve().parent / "models.yaml"


def _load_models() -> dict[str, Any]:
    if not _MODELS_PATH.exists():
        return {"cheap": "openai/gpt-4o-mini", "strong": "openai/gpt-4o"}
    return yaml.safe_load(_MODELS_PATH.read_text(encoding="utf-8"))


def pick_model(tier: str) -> str:
    cfg = _load_models()
    if tier == "strong":
        return str(cfg.get("strong", "openai/gpt-4o"))
    return str(cfg.get("cheap", "openai/gpt-4o-mini"))


def _router_auto(prompt_chars: int, tier_hint: str | None) -> str:
    """Длинный контекст или явный strong → strong модель."""
    if tier_hint == "strong":
        return pick_model("strong")
    if prompt_chars > 12000:
        return pick_model("strong")
    return pick_model("cheap")


def estimate_cost_usd(model: str, tokens_in: int | None, tokens_out: int | None) -> float | None:
    """USD по прайсам из models.yaml (USD за 1M токенов). None если прайс не задан."""
    if tokens_in is None and tokens_out is None:
        return None
    cfg = _load_models()
    prices = cfg.get("prices") if isinstance(cfg, dict) else None
    if not isinstance(prices, dict):
        return None
    p = prices.get(model)
    if not isinstance(p, dict):
        return None
    p_in = p.get("in")
    p_out = p.get("out")
    if p_in is None and p_out is None:
        return None
    cost = 0.0
    if tokens_in and p_in is not None:
        cost += (float(tokens_in) / 1_000_000.0) * float(p_in)
    if tokens_out and p_out is not None:
        cost += (float(tokens_out) / 1_000_000.0) * float(p_out)
    return round(cost, 6)


class JSONParseError(ValueError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise JSONParseError(str(e)) from e


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, JSONParseError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
async def chat_json(
    messages: list[dict[str, str]],
    schema: type[T],
    *,
    model: str | None = None,
    tier: str = "cheap",
    run_id: str | None = None,
    vacancy_id: str | None = None,
    function: str = "chat_json",
    auto_router: bool = True,
    temperature: float = 0.2,
    out_model: list[str] | None = None,
) -> T:
    """Вызов OpenRouter Chat Completions, парсинг JSON → pydantic."""
    cfg = _load_models()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY не задан")

    base = os.getenv("OPENROUTER_BASE_URL") or cfg.get("base_url") or "https://openrouter.ai/api/v1"
    base = str(base).rstrip("/")

    prompt_text = "\n".join(m.get("content", "") for m in messages)
    if model is None:
        model = (
            _router_auto(len(prompt_text), "strong" if tier == "strong" else None)
            if auto_router
            else pick_model(tier)
        )

    cache_on = os.getenv("LLM_CACHE", "1") not in ("0", "false", "False")
    url_key = vacancy_id or "no_vacancy"
    ch: str | None = None
    if cache_on:
        cache_key_src = json.dumps(
            {"messages": messages, "model": model, "function": function, "temperature": temperature},
            ensure_ascii=False,
            sort_keys=True,
        )
        ch = compute_content_hash(cache_key_src)
        hit = cache_get(url_key, ch, function)
        if hit is not None:
            if out_model is not None:
                out_model.clear()
                out_model.append(model)
            return schema.model_validate(hit)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://localhost"),
        "X-Title": "Prometheus 2.0",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{base}/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        data = r.json()

    latency_ms = int((time.perf_counter() - t0) * 1000)
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage") or {}
    tokens_in = usage.get("prompt_tokens")
    tokens_out = usage.get("completion_tokens")
    cost_usd = estimate_cost_usd(model, tokens_in, tokens_out)

    try:
        parsed = _extract_json(content)
        result = schema.model_validate(parsed)
    except Exception as e:
        _log_llm_call(
            run_id=run_id,
            vacancy_id=vacancy_id,
            function=function,
            model=model,
            prompt=json.dumps(messages)[:8000],
            response=content[:8000],
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost_usd,
            latency_ms=latency_ms,
            status=f"validate_error: {e}",
        )
        raise

    _log_llm_call(
        run_id=run_id,
        vacancy_id=vacancy_id,
        function=function,
        model=model,
        prompt=json.dumps(messages)[:8000],
        response=content[:4000],
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=cost_usd,
        latency_ms=latency_ms,
        status="ok",
    )

    if run_id:
        log_event(run_id, "llm_call", {"function": function, "model": model})

    if cache_on and ch is not None:
        cache_set(url_key, ch, function, result.model_dump())

    if out_model is not None:
        out_model.clear()
        out_model.append(model)

    return result


def _log_llm_call(
    run_id: str | None,
    vacancy_id: str | None,
    function: str,
    model: str,
    prompt: str,
    response: str,
    tokens_in: int | None,
    tokens_out: int | None,
    cost: float | None,
    latency_ms: int,
    status: str,
) -> None:
    cli = get_supabase()
    if cli is None:
        return
    cli.table("llm_calls").insert(
        {
            "run_id": run_id,
            "vacancy_id": vacancy_id,
            "function": function,
            "model": model,
            "prompt": prompt,
            "response": response,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "latency_ms": latency_ms,
            "status": status,
        }
    ).execute()


async def chat_json_with_fallback(
    messages: list[dict[str, str]],
    schema: type[T],
    *,
    tier: str = "cheap",
    run_id: str | None = None,
    vacancy_id: str | None = None,
    function: str = "chat_json",
    temperature: float = 0.2,
    out_model: list[str] | None = None,
) -> T:
    """Сначала указанный tier; при ошибке парсинга/валидации — strong.
    Если в ответе confidence < 0.6 — один повтор на strong (прометы с низкой уверенностью)."""
    try:
        result = await chat_json(
            messages,
            schema,
            tier=tier,
            run_id=run_id,
            vacancy_id=vacancy_id,
            function=function,
            auto_router=True,
            temperature=temperature,
            out_model=out_model,
        )
    except (JSONParseError, ValueError, httpx.HTTPError):
        return await chat_json(
            messages,
            schema,
            model=pick_model("strong"),
            tier="strong",
            run_id=run_id,
            vacancy_id=vacancy_id,
            function=function + "_fallback",
            auto_router=False,
            temperature=temperature,
            out_model=out_model,
        )
    if schema is ExtractScoring:
        conf = float(getattr(result, "confidence", 1.0) or 1.0)
        if conf < 0.6:
            return await chat_json(
                messages,
                schema,
                model=pick_model("strong"),
                tier="strong",
                run_id=run_id,
                vacancy_id=vacancy_id,
                function=function + "_confidence_retry",
                auto_router=False,
                temperature=temperature,
                out_model=out_model,
            )
    return result
