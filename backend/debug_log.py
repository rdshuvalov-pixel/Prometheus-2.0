from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_LOG_PATH = Path("/Users/luqy/Documents/Cursor/Прометей 2.0/.cursor/debug-9707ab.log")
_SESSION_ID = "9707ab"


def dbg(*, hypothesis_id: str, location: str, message: str, data: dict[str, Any] | None = None, run_id: str | None = None) -> None:
    """Write one NDJSON line. Never include secrets/PII."""
    payload: dict[str, Any] = {
        "sessionId": _SESSION_ID,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    if run_id:
        payload["runId"] = run_id
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _LOG_PATH.open("a", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Debug logging must never break pipeline.
        pass

