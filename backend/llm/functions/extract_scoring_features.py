from __future__ import annotations

from backend.llm.gateway import chat_json_with_fallback
from backend.llm.schemas import BatchExtractScoringResponse, ExtractScoring
from backend.pipeline.batch_llm import build_batch_prompt

SYSTEM = """You extract structured scoring features for a Product Manager vacancy for Ruslan (EU remote/Lisbon hybrid).
Follow Prometei groups A-F. Each metric object must have: value (bool), points (number up to group max), evidence (strings from JD).
Critical keys: product_management, work_format_fit, seniority_fit, full_time, location_fit.
Experience keys: fintech_or_ecommerce, b2b_saas, ownership_roadmap_discovery, responsibility_match, task_match.
Skills keys: analytics, ui_ux, process_design, english_b2, agile, api_integrations, dev_team_collab.
Strategy keys: growth_monetisation, new_product_market, metrics, stakeholders.
Company keys: watchlist_tier, familiar_market, scale_up_plg, senior_compensation.
Bonus keys: known_product, cultural_fit, urgent_hiring.
Also risks[], confidence 0-1. JSON only."""

BATCH_SYSTEM = SYSTEM + (
    "\n\nBatch mode: user message contains ---JOB0---..---JOBn---. "
    'Return JSON object {"items":[...]} with the same number of scoring objects in order.'
)


async def extract_scoring_features(text: str, *, run_id: str | None = None, vacancy_id: str | None = None) -> ExtractScoring:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": text[:14000]},
    ]
    return await chat_json_with_fallback(
        messages,
        ExtractScoring,
        run_id=run_id,
        vacancy_id=vacancy_id,
        function="extract_scoring_features",
    )


async def extract_scoring_features_batch(
    blocks: list[str],
    *,
    run_id: str | None = None,
    vacancy_ids: list[str | None] | None = None,
) -> list[ExtractScoring]:
    n = len(blocks)
    if n == 0:
        return []
    if n == 1:
        return [
            await extract_scoring_features(
                blocks[0], run_id=run_id, vacancy_id=(vacancy_ids[0] if vacancy_ids else None)
            )
        ]
    user_block = f"Count={n}.\n" + build_batch_prompt(blocks)
    messages = [
        {"role": "system", "content": BATCH_SYSTEM},
        {"role": "user", "content": user_block[:50000]},
    ]
    primary_vid = (vacancy_ids[0] if vacancy_ids else None) if vacancy_ids else None
    out = await chat_json_with_fallback(
        messages,
        BatchExtractScoringResponse,
        run_id=run_id,
        vacancy_id=primary_vid,
        function="extract_scoring_features_batch",
    )
    if len(out.items) != n:
        raise ValueError(f"batch size mismatch: expected {n}, got {len(out.items)}")
    return list(out.items)
