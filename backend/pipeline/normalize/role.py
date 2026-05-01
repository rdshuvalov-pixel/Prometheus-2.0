from __future__ import annotations

import re

PRODUCT_ROLE_RE = re.compile(
    r"(?i)\b("
    r"product\s+(manager|lead|owner|head|director)|"
    r"senior\s+product\s+manager|"
    r"group\s+product\s+manager|"
    r"principal\s+product\s+manager|"
    r"staff\s+product\s+manager"
    r")\b"
)

NON_PRODUCT_TITLE_BLOCK = re.compile(
    r"(?i)\b("
    r"project\s+manager|"
    r"delivery\s+manager|"
    r"scrum\s+master|"
    r"engineering\s+manager|"
    r"marketing\s+manager|"
    r"operations\s+manager|"
    r"growth\s+manager|"
    r"product\s+designer|"
    r"product\s+marketing"
    r")\b"
)


def is_product_title(role_title: str, description: str = "") -> bool:
    text = f"{role_title}\n{description}"
    if NON_PRODUCT_TITLE_BLOCK.search(role_title):
        if PRODUCT_ROLE_RE.search(role_title):
            return True
        return False
    return bool(PRODUCT_ROLE_RE.search(text))


def extract_normalized_role(role_title: str) -> str:
    if PRODUCT_ROLE_RE.search(role_title):
        m = PRODUCT_ROLE_RE.search(role_title)
        if m:
            return m.group(0).strip()
    return role_title.strip()
