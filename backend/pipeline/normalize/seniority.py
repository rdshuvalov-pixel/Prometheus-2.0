from __future__ import annotations

import re

SENIOR_RE = re.compile(
    r"(?i)\b(senior|sr\.?|lead|head|principal|staff|group)\b"
)
MID_RE = re.compile(r"(?i)\b(mid|middle|intermediate)\b")
JUNIOR_RE = re.compile(r"(?i)\b(junior|associate|intern|graduate)\b")


def detect_seniority(title: str, description: str = "") -> str:
    t = f"{title} {description}"
    if JUNIOR_RE.search(t):
        return "junior"
    if SENIOR_RE.search(title) or SENIOR_RE.search(description[:500]):
        return "senior"
    if MID_RE.search(t):
        return "mid"
    return "unknown"
