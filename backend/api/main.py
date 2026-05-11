"""uvicorn backend.api.main:app --host 0.0.0.0 --port 8080"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel

from backend.db.client import finish_run, get_supabase, insert_run, log_event, merge_run_metrics
from backend.scoring.preview import compare_overrides
from backend.writer.formal import generate_formal
from backend.writer.profile_loader import load_profile_for_writing

ROOT = Path(__file__).resolve().parents[2]
CRAWL_BATCH_SIZE = "50"

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
    log_event(
        run_id,
        "full_queued",
        {
            "profile_id": x_profile_id,
            "steps": ["crawl", "crawl_filter", "enrich_texts", "llm_normalize", "dedup_master", "score", "promote", "report"],
        },
    )
    steps = [
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_crawl",
            "--tier",
            "all",
            "--concurrency",
            "4",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
            "--batch-size",
            CRAWL_BATCH_SIZE,
            "--all-batches",
            "--to-stage",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_crawl_filter_stage",
            "--drain",
            "--batch",
            "100",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_enrich_texts_stage",
            "--drain",
            "--batch",
            "40",
            "--delay",
            "0.2",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_llm_normalize_stage",
            "--drain",
            "--batch",
            "10",
            "--delay",
            "0.25",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_dedup_master_stage",
            "--batch",
            "200",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_score_stage",
            "--drain",
            "--batch",
            "50",
            "--chunk-size",
            "5",
            "--delay",
            "0.2",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_promote",
            "--threshold",
            "50",
            "--batch",
            "200",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
        [
            sys.executable,
            "-m",
            "backend.pipeline.run_report",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ],
    ]
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    if x_profile_id:
        env["ACTIVE_PROFILE_ID"] = x_profile_id

    def _runner() -> None:
        started = time.time()
        merge_run_metrics(run_id or "", {"mode": "full", "started_at_ts": started})
        status = "ok"
        for cmd in steps:
            step_name = cmd[3].split(".")[-1].removeprefix("run_") if len(cmd) > 3 else "step"
            step_started = time.time()
            log_event(run_id, f"step_{step_name}_started", {"cmd": cmd})
            proc = subprocess.run(cmd, cwd=str(ROOT), env=env, check=False, capture_output=True, text=True)
            elapsed_ms = int((time.time() - step_started) * 1000)
            merge_run_metrics(
                run_id or "",
                {f"{step_name}_exit_code": proc.returncode, f"{step_name}_elapsed_ms": elapsed_ms},
            )
            if proc.returncode == 0:
                log_event(run_id, f"step_{step_name}_done", {"elapsed_ms": elapsed_ms})
            else:
                status = "error"
                log_event(
                    run_id,
                    f"step_{step_name}_error",
                    {
                        "elapsed_ms": elapsed_ms,
                        "exit_code": proc.returncode,
                        "stderr_tail": (proc.stderr or "")[-2000:],
                        "stdout_tail": (proc.stdout or "")[-2000:],
                    },
                    level="error",
                )
        if run_id:
            finished = time.time()
            merge_run_metrics(
                run_id,
                {"finished_at_ts": finished, "elapsed_ms": int((finished - started) * 1000)},
            )
            finish_run(run_id, status, metrics={})

    bg.add_task(_runner)
    return {"status": "queued", "run_id": run_id or ""}


@app.post("/vacancies/{vacancy_id}/generate/formal")
async def generate_cover_formal(
    vacancy_id: str,
    authorization: str | None = Header(default=None),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> dict[str, str]:
    _auth(authorization)
    if not os.getenv("OPENROUTER_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY missing")

    env = {**os.environ}
    if x_profile_id:
        env["ACTIVE_PROFILE_ID"] = x_profile_id

    cli = get_supabase()
    if cli is None:
        raise HTTPException(status_code=500, detail="SUPABASE not configured")

    res = cli.table("vacancies").select("id, company, role_title, description, status, score").eq("id", vacancy_id).single().execute()
    v = getattr(res, "data", None) or None
    if not v:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    if str(v.get("status")) != "Scored" or (v.get("score") is not None and int(v.get("score")) < 50):
        raise HTTPException(status_code=400, detail="Vacancy is not eligible for cover letter")

    profile = load_profile_for_writing()
    block = f"{v.get('role_title','')}\n{v.get('company','')}\n{v.get('description','')}"
    body = await generate_formal(
        profile.resume_md,
        profile.interview_md,
        profile.work_history_md,
        block,
        run_id=None,
        vacancy_id=str(v.get("id")),
    )
    cli.table("cover_letters").upsert(
        {"vacancy_id": str(v.get("id")), "kind": "formal", "body": body, "model": "openrouter"},
        on_conflict="vacancy_id,kind",
    ).execute()
    return {"status": "ok"}


def _queue_step(bg: BackgroundTasks, *, step: str, args: list[str], run_id: str | None, x_profile_id: str | None) -> str:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    if x_profile_id:
        env["ACTIVE_PROFILE_ID"] = x_profile_id
    log_event(run_id, f"step_{step}_queued", {"args": args})

    def _runner() -> None:
        t0 = time.time()
        log_event(run_id, f"step_{step}_started", {})
        proc = subprocess.run(args, cwd=str(ROOT), env=env, check=False, capture_output=True, text=True)
        elapsed_ms = int((time.time() - t0) * 1000)
        merge_run_metrics(run_id or "", {f"{step}_exit_code": proc.returncode, f"{step}_elapsed_ms": elapsed_ms})
        if proc.returncode == 0:
            log_event(run_id, f"step_{step}_done", {"elapsed_ms": elapsed_ms})
        else:
            log_event(
                run_id,
                f"step_{step}_error",
                {
                    "elapsed_ms": elapsed_ms,
                    "exit_code": proc.returncode,
                    "stderr_tail": (proc.stderr or "")[-2000:],
                    "stdout_tail": (proc.stdout or "")[-2000:],
                },
                level="error",
            )
        if run_id:
            finish_run(run_id, "ok" if proc.returncode == 0 else "error", metrics={})

    bg.add_task(_runner)
    return run_id or ""


@app.post("/pipeline/step/{name}")
async def pipeline_step(
    name: str,
    bg: BackgroundTasks,
    authorization: str | None = Header(default=None),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> dict[str, str]:
    _auth(authorization)
    run_id = insert_run(x_profile_id) if x_profile_id else insert_run(None)
    if name == "crawl":
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_crawl",
            "--tier",
            "all",
            "--concurrency",
            "4",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
            "--batch-size",
            CRAWL_BATCH_SIZE,
            "--all-batches",
            "--to-stage",
        ]
    elif name in ("crawl_filter", "filter_crawl", "post_crawl_filter"):
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_crawl_filter_stage",
            "--drain",
            "--batch",
            "100",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name == "normalize":
        args = [sys.executable, "-m", "backend.pipeline.run_normalize", "--profile-id", x_profile_id or ""]
    elif name in ("enrich_texts", "enrich"):
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_enrich_texts_stage",
            "--drain",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name in ("normalize_jobs", "llm_normalize"):
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_llm_normalize_stage",
            "--drain",
            "--run-id",
            run_id or "",
            "--timeout-s",
            "90",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name in ("deduplicate_jobs", "dedup_master"):
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_dedup_master_stage",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name == "dedup":
        args = [sys.executable, "-m", "backend.pipeline.run_dedup_stage", "--profile-id", x_profile_id or ""]
    elif name == "score":
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_score_stage",
            "--drain",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name == "promote":
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_promote",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name == "report":
        args = [
            sys.executable,
            "-m",
            "backend.pipeline.run_report",
            "--run-id",
            run_id or "",
            "--profile-id",
            x_profile_id or "",
        ]
    elif name in ("check_status", "status"):
        args = [sys.executable, "-m", "backend.pipeline.run_check_status_stage", "--profile-id", x_profile_id or ""]
    else:
        raise HTTPException(status_code=404, detail="Unknown step")

    rid = _queue_step(bg, step=name, args=args, run_id=run_id, x_profile_id=x_profile_id)
    return {"status": "queued", "run_id": rid}
