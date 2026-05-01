# MVP: Vercel, RLS strict, VPS, E2E

Выполняется вручную после локального прогона пайплайна и заполненного `.env`.

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

## VPS (backend API + таймер)

1. `git clone` репозитория на сервер, `cp .env.example .env`, те же ключи что локально.
2. `bash infra/bootstrap.sh` — API на порту **8080** (см. [infra/bootstrap.sh](../infra/bootstrap.sh)).
3. Откройте firewall для 8080 или поставьте reverse proxy + TLS.
4. Systemd:

```bash
sudo cp infra/prometheus-pipeline.service infra/prometheus-pipeline.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now prometheus-pipeline.timer
sudo systemctl status prometheus-pipeline.timer
```

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

В UI: главная / дашборд с `pipeline_runs`, `/vacancies` — строки со score и ссылки на cover letters.
