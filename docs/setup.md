# Настройка

1. Создайте проект в Supabase, примените миграции из `db/migrations/` по порядку.
2. Скопируйте `.env.example` → `.env`, укажите ключи.
3. `uv sync` в корне репозитория.
4. `uv run python -m backend.scripts.seed_profile` — загрузка профиля Руслана (после миграций).
5. Frontend: `cd frontend && npm install`, добавьте `NEXT_PUBLIC_SUPABASE_URL` и `NEXT_PUBLIC_SUPABASE_ANON_KEY` в `frontend/.env.local`.
