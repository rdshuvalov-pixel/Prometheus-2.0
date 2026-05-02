from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import dateparser

from backend.models.raw import RawVacancy

MAX_JOBS_PER_TARGET = 15

_DESCRIPTION_SELECTORS = (
    "[data-cy=job-description]",
    "[data-testid*=job-description]",
    "[data-testid*=JobDescription]",
    "article",
    "main",
    ".section-block",
    "[class*=job-description]",
    "[class*=JobDescription]",
    "[class*=description]",
)


async def _extract_description(page) -> str:
    for sel in _DESCRIPTION_SELECTORS:
        try:
            txt = (await page.locator(sel).first.inner_text(timeout=8000)).strip()
            if len(txt) > 200:
                return txt[:8000]
        except Exception:
            continue
    try:
        body = (await page.locator("body").inner_text(timeout=10000)).strip()
        return body[:8000]
    except Exception:
        return ""


async def _extract_location_line(page) -> str:
    for sel, is_meta in (
        ('meta[property="og:locality"]', True),
        ('meta[name="geo.placename"]', True),
        ("[class*=location]", False),
        ("header h2", False),
        ("h2", False),
    ):
        try:
            loc = page.locator(sel).first
            if is_meta:
                c = await loc.get_attribute("content")
                if c and len(c.strip()) > 1:
                    return c.strip()[:500]
            else:
                txt = (await loc.inner_text(timeout=3000)).strip()
                if 2 < len(txt) < 300:
                    return txt
        except Exception:
            continue
    return ""


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw or not raw.strip():
        return None
    dt = dateparser.parse(raw.strip())
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def _extract_posted_at(page) -> datetime | None:
    candidates: list[str] = []
    for prop in ("article:published_time", "og:updated_time"):
        try:
            c = await page.locator(f'meta[property="{prop}"]').first.get_attribute("content")
            if c:
                candidates.append(c)
        except Exception:
            pass
    try:
        times = page.locator("time[datetime]")
        n = await times.count()
        for i in range(min(n, 5)):
            dt_attr = await times.nth(i).get_attribute("datetime")
            if dt_attr:
                candidates.append(dt_attr)
            try:
                txt = (await times.nth(i).inner_text()).strip()
                if txt:
                    candidates.append(txt)
            except Exception:
                pass
    except Exception:
        pass
    for raw in candidates:
        parsed = _parse_datetime(raw)
        if parsed:
            return parsed
    return None


async def _extract_job_page(page, href: str) -> tuple[str, str, datetime | None]:
    try:
        await page.goto(href, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(0.35)
    except Exception:
        return "", "", None
    description = await _extract_description(page)
    location = await _extract_location_line(page)
    posted_at = await _extract_posted_at(page)
    return description, location, posted_at


async def fetch_with_playwright(url: str, company_name: str, tier: str) -> list[RawVacancy]:
    """Открывает страницу каталога, затем до MAX_JOBS_PER_TARGET страниц вакансий — описание/локация/дата."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []

    out: list[RawVacancy] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            links = await page.eval_on_selector_all(
                "a[href*='job'], a[href*='career'], a[href*='vacancy']",
                "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))",
            )
        except Exception:
            await browser.close()
            return []

        seen: set[str] = set()
        candidates: list[dict[str, str]] = []
        for item in links:
            href = (item.get("href") or "").strip()
            text = (item.get("text") or "").strip()
            if not href or len(text) < 3:
                continue
            if href in seen:
                continue
            seen.add(href)
            tl = text.lower()
            if "product" not in tl and "pm" not in tl:
                continue
            candidates.append({"href": href, "text": text})
            if len(candidates) >= MAX_JOBS_PER_TARGET * 4:
                break

        shortlist = candidates[:MAX_JOBS_PER_TARGET]

        for c in shortlist:
            desc, loc, posted = await _extract_job_page(page, c["href"])
            out.append(
                RawVacancy(
                    title=c["text"][:200],
                    company=company_name,
                    description=desc,
                    location=loc,
                    posted_at=posted,
                    url=c["href"],
                    source="playwright",
                    tier=tier,
                    ats_type=None,
                )
            )
            await asyncio.sleep(0.15)

        await browser.close()

    return out
