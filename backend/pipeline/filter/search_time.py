from __future__ import annotations

from backend.pipeline.normalize.role import NON_PRODUCT_TITLE_BLOCK, PRODUCT_ROLE_RE


def keyword_matches_title(role_title: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lt = role_title.lower()
    for kw in keywords:
        if kw.lower() in lt:
            return True
    return False


def search_time_exclude_obvious_non_product(role_title: str) -> tuple[bool, str | None]:
    """Сразу исключить очевидные не-PM роли по названию."""
    if PRODUCT_ROLE_RE.search(role_title):
        return True, None
    if NON_PRODUCT_TITLE_BLOCK.search(role_title):
        return False, "search_role_excluded"
    return True, None


def passes_search_filters(role_title: str, keywords: list[str]) -> tuple[bool, str | None]:
    ok, reason = search_time_exclude_obvious_non_product(role_title)
    if not ok:
        return False, reason
    if not keyword_matches_title(role_title, keywords):
        return False, "search_role_excluded"
    return True, None
