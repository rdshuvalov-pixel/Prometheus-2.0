#!/usr/bin/env bash
# Crawl → vacancies_stage (без enrich/LLM/score/promote). Вызывается вручную или из systemd,
# если вы сами включили таймер и задали расписание в prometheus-pipeline.timer.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

DC=(docker compose)
EXEC=("${DC[@]}" exec -T api)

CRAWL_CONCURRENCY="${CRAWL_CONCURRENCY:-4}"
CRAWL_TARGET_TIMEOUT_S="${CRAWL_TARGET_TIMEOUT_S:-120}"

echo "[run_crawl_stage] starting"
"${EXEC[@]}" python -m backend.pipeline.run_crawl \
  --tier all \
  --limit 0 \
  --concurrency "$CRAWL_CONCURRENCY" \
  --target-timeout-s "$CRAWL_TARGET_TIMEOUT_S" \
  --to-stage
echo "[run_crawl_stage] done"

