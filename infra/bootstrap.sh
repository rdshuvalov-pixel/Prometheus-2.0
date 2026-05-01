#!/usr/bin/env bash
set -euo pipefail
# Запуск на VPS: установка Docker (если нет), клонирование репо, копирование .env

if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR/infra"
docker compose build
docker compose up -d api
echo "API на порту 8080. Добавьте systemd unit для cron."
