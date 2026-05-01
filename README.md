# Прометей 2.0

Монорепо: автоматический поиск и скоринг вакансий PM (Prometei).

- `backend/` — Python: пайплайн, краулеры, LLM Gateway, скоринг
- `frontend/` — Next.js (App Router), дашборд
- `db/migrations/` — SQL для Supabase
- `seeds/` — профиль кандидата и данные
- `infra/` — Docker, systemd, bootstrap VPS

## Требования

- Python **3.10+** (рекомендуется 3.11), Node 18+ для frontend.
- Зависимости краулера: `pip install -e ".[dev,crawl]"` (JobSpy, Playwright).

## Быстрый старт

```bash
cp .env.example .env
# заполнить ключи OpenRouter и Supabase

pip install hatchling && pip install -e ".[dev,crawl]"
PYTHONPATH=. pytest backend/tests -q

cd frontend && npm install && npm run dev
```

Деплой UI: в Vercel root directory = `frontend`, переменные `NEXT_PUBLIC_SUPABASE_*`, `SUPABASE_SERVICE_ROLE_KEY`, опционально `PROMETHEUS_API_URL` (Preview весов).

См. `docs/setup.md`, чеклист продакшена — `docs/BLOCK_B_DEPLOY.md`.
