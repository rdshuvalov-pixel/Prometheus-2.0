"""python -m backend.pipeline.run_llm_normalize_stage

TЗ step #3: LLM normalization of stage vacancies into structured fields.
Input: `vacancies_stage` rows with page_text_full present and normalized_payload is null.
Output: normalized_* columns + normalized_payload + normalization_confidence + pipeline_status.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timezone

from backend.db.client import apply_active_profile_id, get_active_profile, get_supabase, merge_run_metrics
from backend.llm.functions.normalize_vacancy import normalize_vacancy


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _dbg(hypothesis_id: str, location: str, message: str, data: dict, run_id: str | None) -> None:
    # region agent log
    import json as _json
    from pathlib import Path

    try:
        Path("/Users/luqy/Documents/Cursor/Прометей 2.0/.cursor").mkdir(parents=True, exist_ok=True)
        Path("/Users/luqy/Documents/Cursor/Прометей 2.0/.cursor/debug-9707ab.log").open("a", encoding="utf-8").write(
            _json.dumps(
                {
                    "sessionId": "9707ab",
                    "hypothesisId": hypothesis_id,
                    "location": location,
                    "message": message,
                    "data": data,
                    "runId": run_id,
                    "timestamp": int(time.time() * 1000),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    except Exception:
        pass
    # endregion


def _merge_warnings(existing: object, *codes: str) -> list[str]:
    cur = list(existing) if isinstance(existing, list) else []
    out = [*cur]
    for c in codes:
        if c not in out:
            out.append(c)
    return out


async def main_async(args: argparse.Namespace) -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        print(json.dumps({"error": "OPENROUTER_API_KEY missing"}, ensure_ascii=False))
        return

    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    normalized = 0
    errors = 0
    while True:
        q = (
            cli.table("vacancies_stage")
            .select(
                "id, url, platform, company, company_name, role_title, job_title, "
                "description, page_text_full, location_raw, warnings, created_at"
            )
            .eq("profile_id", profile_id)
            .eq("status", "Staged")
            .neq("page_text_full", "")
            .is_("normalized_payload", "null")
            .order("created_at", desc=False)
            .limit(max(1, int(args.batch)))
        )
        res = q.execute()
        rows = getattr(res, "data", None) or []
        _dbg(
            "H1",
            "backend/pipeline/run_llm_normalize_stage.py:query",
            "selected_rows",
            {"rows": len(rows), "batch": int(args.batch)},
            args.run_id,
        )
        if not rows:
            if args.run_id:
                merge_run_metrics(args.run_id, {"stage_llm_normalized": normalized, "stage_llm_errors": errors})
            print(json.dumps({"normalized": normalized, "errors": errors}, ensure_ascii=False))
            return

        for v in rows:
            sid = v.get("id")
            if not sid:
                continue
            url = (v.get("url") or "").strip()
            now = _utc_iso()
            try:
                _dbg(
                    "H2",
                    "backend/pipeline/run_llm_normalize_stage.py:normalize_one",
                    "normalize_start",
                    {
                        "id": str(sid),
                        "url": url[:300],
                        "page_text_full_len": len((v.get("page_text_full") or "")),
                        "desc_len": len((v.get("description") or "")),
                        "timeout_s": int(args.timeout_s),
                    },
                    args.run_id,
                )
                t0 = time.time()
                out = await normalize_vacancy(
                    job_title=(v.get("job_title") or v.get("role_title") or ""),
                    company_name=(v.get("company_name") or v.get("company") or ""),
                    job_url=url,
                    job_description=(v.get("description") or ""),
                    page_text_full=(v.get("page_text_full") or ""),
                    location_raw=(v.get("location_raw") or ""),
                    platform=(v.get("platform") or ""),
                    run_id=args.run_id,
                    vacancy_id=str(sid),
                ) if args.timeout_s <= 0 else await asyncio.wait_for(
                    normalize_vacancy(
                        job_title=(v.get("job_title") or v.get("role_title") or ""),
                        company_name=(v.get("company_name") or v.get("company") or ""),
                        job_url=url,
                        job_description=(v.get("description") or ""),
                        page_text_full=(v.get("page_text_full") or ""),
                        location_raw=(v.get("location_raw") or ""),
                        platform=(v.get("platform") or ""),
                        run_id=args.run_id,
                        vacancy_id=str(sid),
                    ),
                    timeout=float(args.timeout_s),
                )
                _dbg(
                    "H3",
                    "backend/pipeline/run_llm_normalize_stage.py:normalize_one",
                    "normalize_returned",
                    {"id": str(sid), "elapsed_ms": int((time.time() - t0) * 1000)},
                    args.run_id,
                )
            except Exception as e:
                errors += 1
                _dbg(
                    "H4",
                    "backend/pipeline/run_llm_normalize_stage.py:normalize_one",
                    "normalize_error",
                    {"id": str(sid), "error_type": type(e).__name__, "error": str(e)[:800]},
                    args.run_id,
                )
                cli.table("vacancies_stage").update(
                    {
                        "warnings": _merge_warnings(v.get("warnings"), "llm_normalize_failed"),
                        "pipeline_status": "NormalizeFailed",
                        "updated_at": now,
                    }
                ).eq("id", sid).execute()
                if args.verbose:
                    print(f"normalize failed {url}: {e}")
                await asyncio.sleep(args.delay)
                continue

            payload = out.model_dump()
            _dbg(
                "H5",
                "backend/pipeline/run_llm_normalize_stage.py:normalize_one",
                "normalize_ok",
                {"id": str(sid), "confidence": payload.get("normalization_confidence")},
                args.run_id,
            )
            cli.table("vacancies_stage").update(
                {
                    "normalized_payload": payload,
                    "normalized_title": payload.get("normalized_title"),
                    "seniority": payload.get("seniority"),
                    "function": payload.get("function"),
                    "domain": payload.get("domain"),
                    "industry": payload.get("industry"),
                    "employment_type": payload.get("employment_type"),
                    "work_format": payload.get("work_format"),
                    "location_normalized": payload.get("location_normalized"),
                    "country": payload.get("country"),
                    "remote_allowed": payload.get("remote_allowed"),
                    "hybrid_allowed": payload.get("hybrid_allowed"),
                    "relocation_required": payload.get("relocation_required"),
                    "salary_min": payload.get("salary_min"),
                    "salary_max": payload.get("salary_max"),
                    "salary_currency": payload.get("salary_currency"),
                    "english_required": payload.get("english_required"),
                    "product_type": payload.get("product_type"),
                    "b2b_or_b2c": payload.get("b2b_or_b2c"),
                    "ai_related": payload.get("ai_related"),
                    "fintech_related": payload.get("fintech_related"),
                    "growth_related": payload.get("growth_related"),
                    "monetization_related": payload.get("monetization_related"),
                    "platform_related": payload.get("platform_related"),
                    "technical_depth": payload.get("technical_depth"),
                    "management_scope": payload.get("management_scope"),
                    "must_have_requirements": payload.get("must_have_requirements") or [],
                    "nice_to_have_requirements": payload.get("nice_to_have_requirements") or [],
                    "responsibilities": payload.get("responsibilities") or [],
                    "red_flags": payload.get("red_flags") or [],
                    "positive_signals": payload.get("positive_signals") or [],
                    "normalization_confidence": payload.get("normalization_confidence"),
                    "pipeline_status": "Normalized",
                    "updated_at": now,
                }
            ).eq("id", sid).execute()
            normalized += 1
            await asyncio.sleep(args.delay)

        if not args.drain:
            if args.run_id:
                merge_run_metrics(args.run_id, {"stage_llm_normalized": normalized, "stage_llm_errors": errors})
            print(json.dumps({"normalized": normalized, "errors": errors}, ensure_ascii=False))
            return


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--delay", type=float, default=0.25)
    p.add_argument("--run-id", dest="run_id", default=None)
    p.add_argument("--drain", action="store_true")
    p.add_argument("--profile-id", dest="profile_id", default=None)
    p.add_argument("--timeout-s", dest="timeout_s", type=int, default=90, help="Timeout per vacancy LLM normalize (0 = no timeout)")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

