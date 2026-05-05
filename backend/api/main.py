"""uvicorn backend.api.main:app --host 0.0.0.0 --port 8080"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel

from backend.db.client import finish_run, insert_run
from backend.scoring.preview import compare_overrides

ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="Prometheus 2.0 API", version="0.1.0")


class ScoringPreviewBody(BaseModel):
    scoring_overrides: dict[str, Any] | None = None


def _auth(authorization: str | None) -> None:
    secret = os.getenv("PIPELINE_API_SECRET")
    if not secret:
        return
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scoring/preview")
def scoring_preview(body: ScoringPreviewBody) -> dict[str, Any]:
    return compare_overrides(body.scoring_overrides)


@app.post("/pipeline/run")
async def pipeline_run(
    tier: str = "1",
    authorization: str | None = Header(default=None),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> dict[str, str]:
    _auth(authorization)
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    if x_profile_id:
        env["ACTIVE_PROFILE_ID"] = x_profile_id
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "backend.pipeline.run_crawl",
        "--tier",
        tier,
        cwd=str(ROOT),
        env=env,
    )
    await proc.communicate()
    return {"status": "started" if proc.returncode == 0 else "error", "code": str(proc.returncode)}


@app.post("/pipeline/full")
async def pipeline_full(
    bg: BackgroundTasks,
    authorization: str | None = Header(default=None),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> dict[str, str]:
    _auth(authorization)
    run_id = insert_run(x_profile_id) if x_profile_id else insert_run(None)
    steps = [
        [sys.executable, "-m", "backend.pipeline.run_crawl", "--tier", "all", "--concurrency", "4", "--profile-id", x_profile_id or ""],
        [sys.executable, "-m", "backend.pipeline.run_enrich", "--drain", "--batch", "40", "--rps", "0.15", "--run_id", run_id or ""],
        [sys.executable, "-m", "backend.pipeline.run_score", "--drain", "--batch", "50", "--batch-mode", "--chunk-size", "5", "--delay", "0.2", "--run_id", run_id or ""],
        [sys.executable, "-m", "backend.pipeline.run_write", "--drain", "--batch", "15", "--delay", "0.15", "--run_id", run_id or ""],
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    if x_profile_id:
        env["ACTIVE_PROFILE_ID"] = x_profile_id

    def _runner() -> None:
        for cmd in steps:
            subprocess.run(cmd, cwd=str(ROOT), env=env, check=False)
        if run_id:
            finish_run(run_id, "ok", metrics={})

    bg.add_task(_runner)
    return {"status": "queued", "run_id": run_id or ""}
