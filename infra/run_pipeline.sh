#!/usr/bin/env bash
# Полный прогон: crawl по tier 1–4, затем enrich / score / write (всё в контейнере api).
# Вызывать из systemd (см. prometheus-pipeline.service) или вручную: bash infra/run_pipeline.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

DC=(docker compose)
EXEC=("${DC[@]}" exec -T api)
LIMIT_TIER4="${LIMIT_TIER4:-50}"
CRAWL_CONCURRENCY="${CRAWL_CONCURRENCY:-4}"
CRAWL_TARGET_TIMEOUT_S="${CRAWL_TARGET_TIMEOUT_S:-120}"

run() {
  echo "[run_pipeline] $*"
  if ! "$@"; then
    echo "[run_pipeline] step failed: $*"
  fi
}

run "${EXEC[@]}" python -m backend.pipeline.run_crawl --tier 1 --limit 0 --concurrency "$CRAWL_CONCURRENCY" --target-timeout-s "$CRAWL_TARGET_TIMEOUT_S"
run "${EXEC[@]}" python -m backend.pipeline.run_crawl --tier 2 --limit 0 --concurrency "$CRAWL_CONCURRENCY" --target-timeout-s "$CRAWL_TARGET_TIMEOUT_S"
run "${EXEC[@]}" python -m backend.pipeline.run_crawl --tier 3 --limit 0 --concurrency "$CRAWL_CONCURRENCY" --target-timeout-s "$CRAWL_TARGET_TIMEOUT_S"
run "${EXEC[@]}" python -m backend.pipeline.run_crawl --tier 4 --limit "$LIMIT_TIER4"
run "${EXEC[@]}" python -m backend.pipeline.run_enrich --batch 100 --drain
run "${EXEC[@]}" python -m backend.pipeline.run_score --batch 100 --drain --batch-mode --chunk-size 10 --delay 0.15
# cover letter generation is on-demand (per-vacancy), not part of the default pipeline
