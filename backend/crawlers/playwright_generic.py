from __future__ import annotations

from backend.models.raw import RawVacancy


async def fetch_with_playwright(url: str, company_name: str, tier: str) -> list[RawVacancy]:
    """Открывает страницу и собирает ссылки на вакансии (когда установлен playwright)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return []

    out: list[RawVacancy] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=60000)
        links = await page.eval_on_selector_all(
            "a[href*='job'], a[href*='career'], a[href*='vacancy']",
            "els => els.map(e => ({href: e.href, text: e.innerText.trim()}))",
        )
        await browser.close()
    for item in links[:50]:
        href = item.get("href") or ""
        text = item.get("text") or ""
        if not href or len(text) < 3:
            continue
        if "product" not in text.lower() and "pm" not in text.lower():
            continue
        out.append(
            RawVacancy(
                title=text[:200],
                company=company_name,
                description="",
                location="",
                posted_at=None,
                url=href,
                source="playwright",
                tier=tier,
                ats_type=None,
            )
        )
    return out
