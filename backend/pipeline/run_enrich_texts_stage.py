"""python -m backend.pipeline.run_enrich_texts_stage

Stage enrich step (TЗ #2): fetch full vacancy page text + blocks into `vacancies_stage`.

Updates (best-effort):
- page_text_full
- page_text_header
- page_text_sidebar
- page_text_extra (json)
- description (if empty/too short)
- pipeline_status (to 'Enriched' when succeeded)

Does NOT run automatically; intended to be triggered manually (API/UI).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone

from backend.db.client import (
    apply_active_profile_id,
    get_active_profile,
    get_supabase,
    merge_run_metrics,
)
from backend.pipeline.crawl_constants import PIPELINE_AFTER_CRAWL_FILTER


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_warnings(existing: object, *codes: str) -> list[str]:
    cur = list(existing) if isinstance(existing, list) else []
    out = [*cur]
    for c in codes:
        if c not in out:
            out.append(c)
    return out


async def _extract_texts_playwright(url: str) -> dict[str, object]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "playwright_not_installed"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(25_000)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            await asyncio.sleep(0.35)
        except Exception as e:
            await browser.close()
            return {"error": f"goto_failed: {e}"}

        async def safe_inner_text(sel: str, *, limit: int) -> str:
            try:
                txt = (await page.locator(sel).first.inner_text(timeout=5000)).strip()
                return txt[:limit]
            except Exception:
                return ""

        # Full page body text.
        page_full = await safe_inner_text("body", limit=25_000)
        header = await safe_inner_text("header", limit=6_000)
        sidebar = await safe_inner_text("aside", limit=6_000)

        # Try best-effort primary description extraction (if present).
        description = ""
        for sel in (
            "[data-cy=job-description]",
            "[data-testid*=job-description]",
            "[data-testid*=JobDescription]",
            "[class*=job-description]",
            "[class*=JobDescription]",
            "article",
            "main",
        ):
            description = await safe_inner_text(sel, limit=10_000)
            if len(description) > 300:
                break

        # Extra blocks: common locations where metadata lives.
        extra: dict[str, str] = {}
        for name, sel in (
            ("meta", "main"),
            ("footer", "footer"),
            ("top_h1", "h1"),
            ("top_h2", "h2"),
        ):
            t = await safe_inner_text(sel, limit=2_000)
            if t:
                extra[name] = t

        await browser.close()
        return {
            "page_text_full": page_full,
            "page_text_header": header,
            "page_text_sidebar": sidebar,
            "page_text_extra": extra,
            "description": description,
        }


async def main_async(args: argparse.Namespace) -> None:
    apply_active_profile_id(args.profile_id)
    profile = get_active_profile()
    profile_id = str(profile.id) if profile.id else None
    cli = get_supabase()
    if cli is None or not profile_id:
        print(json.dumps({"error": "no_supabase_or_profile"}, ensure_ascii=False))
        return

    enriched = 0
    errors = 0
    problem_urls: list[str] = []

    while True:
        q = (
            cli.table("vacancies_stage")
            .select("id, url, description, page_text_full, warnings, pipeline_status, created_at")
            .eq("profile_id", profile_id)
            .eq("status", "Staged")
            .eq("pipeline_status", PIPELINE_AFTER_CRAWL_FILTER)
            .or_("page_text_full.is.null,page_text_full.eq.")
            .order("created_at", desc=False)
            .limit(max(1, int(args.batch)))
        )
        res = q.execute()
        rows = getattr(res, "data", None) or []
        if not rows:
            if args.run_id:
                merge_run_metrics(
                    args.run_id,
                    {"stage_enriched": enriched, "stage_enrich_errors": errors, "stage_enrich_problem_urls": problem_urls[:100]},
                )
            print(json.dumps({"enriched": enriched, "errors": errors, "problem_urls": problem_urls[:50]}, ensure_ascii=False))
            return

        for v in rows:
            sid = v.get("id")
            url = (v.get("url") or "").strip()
            if not sid or not url:
                continue
            extracted = await _extract_texts_playwright(url)
            now = _utc_iso()
            if extracted.get("error"):
                errors += 1
                problem_urls.append(url[:1000])
                cli.table("vacancies_stage").update(
                    {
                        "warnings": _merge_warnings(v.get("warnings"), "enrich_failed"),
                        "pipeline_status": v.get("pipeline_status") or "EnrichFailed",
                        "updated_at": now,
                    }
                ).eq("id", sid).execute()
                await asyncio.sleep(args.delay)
                continue

            payload: dict[str, object] = {
                "page_text_full": extracted.get("page_text_full") or "",
                "page_text_header": extracted.get("page_text_header") or "",
                "page_text_sidebar": extracted.get("page_text_sidebar") or "",
                "page_text_extra": extracted.get("page_text_extra") or {},
                "pipeline_status": "Enriched",
                "updated_at": now,
            }
            # If stage.description is empty/very short, replace with extracted description.
            cur_desc = (v.get("description") or "").strip()
            new_desc = (extracted.get("description") or "").strip()
            if len(cur_desc) < 200 and len(new_desc) > len(cur_desc):
                payload["description"] = new_desc[:10_000]

            cli.table("vacancies_stage").update(payload).eq("id", sid).execute()
            enriched += 1
            await asyncio.sleep(args.delay)

        if not args.drain:
            if args.run_id:
                merge_run_metrics(
                    args.run_id,
                    {"stage_enriched": enriched, "stage_enrich_errors": errors, "stage_enrich_problem_urls": problem_urls[:100]},
                )
            print(json.dumps({"enriched": enriched, "errors": errors, "problem_urls": problem_urls[:50]}, ensure_ascii=False))
            return


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=20)
    p.add_argument("--delay", type=float, default=0.2, help="per-item delay in seconds")
    p.add_argument("--run-id", dest="run_id", default=None)
    p.add_argument("--drain", action="store_true")
    p.add_argument("--profile-id", dest="profile_id", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()

