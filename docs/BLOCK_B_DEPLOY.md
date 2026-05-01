# Блок B — боевой MVP (чеклист)

Операции выполняются вручную в вашем аккаунте; репозиторий уже содержит миграции и скрипты.

## B.1 Supabase

1. Создать проект, сохранить `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`.
2. Миграции одним из способов:
   - вставить в SQL Editor файл [db/bundle_migrations_0001_0007.sql](../db/bundle_migrations_0001_0007.sql), или
   - `pip install -e ".[migrate]"` и `DATABASE_URL=... python -m backend.scripts.apply_migrations`
3. После привязки `user_id` к профилю — `0008_rls_strict.sql` (см. [docs/MVP_LAUNCH_REMOTE.md](MVP_LAUNCH_REMOTE.md)).
4. Auth → Email (magic link).

## B.2 GitHub

Приватный репозиторий, `git push` из корня проекта. CI: `.github/workflows/ci.yml`.

## B.3 Окружение

`cp .env.example .env` — заполнить ключи.  
`python -m backend.scripts.seed_profile` — строка `is_default=true` в `candidate_profiles`.

## B.4–B.6 Пайплайн

- `python -m backend.llm.smoke`
- `python -m backend.scripts.build_targets`
- `python -m backend.pipeline.run_crawl --tier 1 --limit 5`
- `python -m backend.pipeline.run_enrich --batch 5`
- `python -m backend.pipeline.run_score --batch 5` (опционально `--batch-mode`)
- `python -m backend.pipeline.run_write --batch 3`  
Для выбранного профиля: `--profile-id <uuid>` или переменная `ACTIVE_PROFILE_ID`.

## B.7 Vercel

Импорт репозитория, root `frontend`. Env: `NEXT_PUBLIC_SUPABASE_*`, `SUPABASE_SERVICE_ROLE_KEY`, `PROMETHEUS_API_URL` (URL backend API для Preview весов).

## B.8 VPS

Клон репозитория, `.env`, `bash infra/bootstrap.sh`.  
Systemd: `infra/prometheus-pipeline.{service,timer}`.

## B.9 E2E

`curl -X POST http://VPS:8080/pipeline/full -H "Authorization: Bearer $PIPELINE_API_SECRET" -H "X-Profile-Id: <uuid>"`  
Проверка UI: последний `pipeline_run`, `/vacancies` с score и письмами.
