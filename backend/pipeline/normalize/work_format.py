from __future__ import annotations

import re

REMOTE_RE = re.compile(
    r"(?i)\b(remote|distributed|work\s+from\s+home|anywhere|worldwide|global\s+remote)\b"
)
HYBRID_RE = re.compile(r"(?i)\bhybrid\b")
OFFICE_RE = re.compile(r"(?i)\b(on-?site|office\b)")


def detect_work_format(text: str) -> str:
    if REMOTE_RE.search(text):
        return "remote"
    if HYBRID_RE.search(text):
        return "hybrid"
    if OFFICE_RE.search(text):
        return "office"
    return "unknown"
