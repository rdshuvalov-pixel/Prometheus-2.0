# MVP: Vercel, RLS strict, VPS, E2E

Выполняется вручную после локального прогона пайплайна и заполненного `.env`.

Чеклист совпадения env VPS/Vercel и смоук прод: [E2E_VERIFICATION.md](./E2E_VERIFICATION.md).

## Локальный прогон (после `SUPABASE_*` + `OPENROUTER_API_KEY` в `.env`)

```bash
python -m backend.scripts.seed_profile
python -m backend.llm.smoke
python -m backend.scripts.build_targets
python -m backend.pipeline.run_crawl --tier 1 --limit 5
python -m backend.pipeline.run_enrich --batch 5
python -m backend.pipeline.run_score --batch 5
python -m backend.pipeline.run_write --batch 3
```

Проверка в Supabase → SQL Editor:

```sql
select count(*) as vacancies from vacancies;
select count(*) as letters from cover_letters;
select id, company, role_title, score, status from vacancies order by created_at desc limit 10;
```

## Vercel (frontend)

1. GitHub: создайте приватный репозиторий, добавьте remote и выполните первый push из корня проекта.
2. Vercel → Add New Project → Import репозитория.
3. **Root Directory:** `frontend`
4. Environment Variables:

| Variable | Значение |
|----------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | из Supabase Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon public |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role (тот же секрет, что `SUPABASE_SERVICE_KEY` в backend `.env`) |
| `PROMETHEUS_API_URL` | после деплоя VPS: `https://your-vps:8080` или временно пропустите Preview весов |
| `PIPELINE_API_SECRET` | server-only: секрет для `/api/pipeline/run` (должен совпадать с `PIPELINE_API_SECRET` на VPS), если задан — включается Bearer-проверка |

5. Deploy → откройте прод-URL, `/login` → magic link.

## RLS strict (после первого логина)

1. В Supabase → Authentication → Users скопируйте UUID залогиненного пользователя.
2. SQL Editor:

```sql
update candidate_profiles
set user_id = '<AUTH_USER_UUID>'::uuid
where is_default = true;
```

3. Примените миграцию строгих политик одним из способов:
   - содержимое [db/migrations/0008_rls_strict.sql](../db/migrations/0008_rls_strict.sql) в SQL Editor, или
   - `DATABASE_URL=... python -m backend.scripts.apply_migrations --include-rls-strict`

## VPS (backend API)

1. `git clone` репозитория на сервер, `cp .env.example .env`, те же ключи что локально.
2. `bash infra/bootstrap.sh` — API на порту **8080** (см. [infra/bootstrap.sh](../infra/bootstrap.sh)).
3. Откройте firewall для 8080 или поставьте reverse proxy + TLS.
4. **Автозапуск пайплайна по расписанию в репозитории отключён** (нет затрат LLM/краула в фоне). Если на сервере уже был включён таймер — отключите: `sudo systemctl disable --now prometheus-pipeline.timer`. Разовый crawl вручную: `sudo systemctl start prometheus-pipeline.service` (после копирования unit-файлов из `infra/`).
5. В Vercel обновите `PROMETHEUS_API_URL` на публичный URL API (если используете Preview весов).

## E2E проверка

Замените `VPS`, `SECRET`, `PROFILE_UUID`:

```bash
curl -sS "http://VPS:8080/health"

curl -sS -X POST "http://VPS:8080/pipeline/full" \
  -H "Authorization: Bearer SECRET" \
  -H "X-Profile-Id: PROFILE_UUID"
```

`PIPELINE_API_SECRET` в `.env` на VPS должен совпадать с `SECRET` в заголовке (если переменная задана; иначе авторизация отключена).

Для запуска пайплайна из UI (скрытая кнопка на главной) в Vercel нужно задать `PIPELINE_API_SECRET` (server-only). Если переменная не задана — endpoint `/api/pipeline/run` будет требовать только активную supabase-сессию, но без дополнительного Bearer-secrets слоя.

В UI: главная / дашборд с `pipeline_runs`, `/vacancies` — строки со score и ссылки на cover letters.
