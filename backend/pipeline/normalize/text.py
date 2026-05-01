from __future__ import annotations

import re


def normalize_company(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_title(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\[\(].*?[\]\)]", "", s).strip()
    return s
