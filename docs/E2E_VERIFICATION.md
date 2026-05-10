# E2E: проверка env, пайплайна и прода

Используй после деплоя Vercel и bootstrap VPS.

## 1. Совпадение Supabase: VPS API ↔ Vercel frontend

Один и тот же проект Supabase:

| Где | Переменная | Должно совпадать |
|-----|------------|------------------|
| VPS `.env` (контейнер `api`) | `SUPABASE_URL` | Тот же хост, что `NEXT_PUBLIC_SUPABASE_URL` на Vercel |
| VPS `.env` | `SUPABASE_SERVICE_KEY` | **service_role** из Dashboard → Settings → API (не anon) |
| Vercel Production | `NEXT_PUBLIC_SUPABASE_URL` | = `SUPABASE_URL` |
| Vercel Production | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | anon public того же проекта |

После правки `.env` на VPS: `cd infra && docker compose up -d`.

**Быстрая проверка:** если после полного прогона пайплайна в SQL Editor `select count(*) from pipeline_runs` = 0, чаще всего на API не заданы `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` или указан другой проект.

## 2. Полный прогон пайплайна (на VPS, внутри контейнера)

Из каталога с `docker-compose.yml` (обычно `infra/`):

```bash
docker compose exec api python -m backend.pipeline.run_crawl --tier 1 --limit 5
docker compose exec api python -m backend.pipeline.run_enrich --batch 5
docker compose exec api python -m backend.pipeline.run_score --batch 5
docker compose exec api python -m backend.pipeline.run_write --batch 3
```

Либо один запрос (если задан `PIPELINE_API_SECRET`):

```bash
curl -sS -X POST "http://127.0.0.1:8080/pipeline/full" \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "X-Profile-Id: YOUR_PROFILE_UUID"
```

## 3. Проверка данных в Supabase (SQL Editor)

```sql
select count(*) as pipeline_runs from pipeline_runs;
select count(*) as vacancies from vacancies;
select count(*) as cover_letters from cover_letters;
```

Ожидается `pipeline_runs >= 1` после успешного crawl; остальное зависит от источников и импорта.

## 4. Проверка прод (ручной смоук)

1. Открыть сайт Vercel → `/` — последний `pipeline_runs` или подсказка, если таблица пуста.
2. `/vacancies` — список строк при наличии данных и RLS `authenticated`.
3. После входа по magic link в шапке: email и кнопка **Выйти**; после **Выйти** — ссылка **Вход**.
4. Опционально: Preview весов на странице профиля (нужен `PROMETHEUS_API_URL` на Vercel).

## 5. Cookies / 500 на страницах и обновление моделей на VPS

После деплоя фронта с `middleware.ts` и `getAll`/`setAll` в `createServerSupabase` ошибка «Cookies can only be modified…» на `/vacancies` должна уйти.

Чтобы в контейнере API подтянулись новые `backend/llm/models.yaml` (Qwen):

```bash
cd /opt/prometheus-20
git pull origin main

cd infra
docker compose build --no-cache api
docker compose up -d --force-recreate api

docker compose exec api cat /app/backend/llm/models.yaml
```

Разовый прогон LLM без кэша (новые вызовы и расчёт `cost` в `llm_calls`):

```bash
docker compose exec -e LLM_CACHE=0 api python -m backend.pipeline.run_enrich --batch 5
docker compose exec -e LLM_CACHE=0 api python -m backend.pipeline.run_score --batch 5
docker compose exec -e LLM_CACHE=0 api python -m backend.pipeline.run_write --batch 3
```

Проверка моделей и стоимости:

```sql
select model,
       count(*) as calls,
       round(sum(coalesce(cost,0))::numeric, 4) as usd
from llm_calls
group by 1
order by 2 desc;
```

## 6. Чистка локационного blacklist (ретро)

После деплоя фильтра `hybrid_reject_locations` старые вакансии с hybrid вне Lisbon (Cyprus / Georgia и т.д.) можно пометить отклонёнными в SQL Editor:

```sql
update vacancies
set status = 'Rejected', reject_reason = 'hybrid_outside_lisbon'
where status in ('New','Scored')
  and (
    lower(description) like '%cyprus%'
    or lower(description) like '%georgia%'
    or lower(description) like '%tbilisi%'
    or lower(description) like '%limassol%'
  )
  and lower(description) like '%hybrid%';
```

Проверьте выборкой перед массовым `update` (`select id, company, role_title from vacancies where …`).

Примените миграцию `db/migrations/0009_country_blacklist.sql` в SQL Editor (код отказа `country_blacklisted` для фильтра локаций).

После деплоя контейнера API (`docker compose build api && docker compose up -d --force-recreate api`) `run_crawl` пишет события `target_started`, `target_done`, `vacancy_rejected` — на дашборде появится таблица «По площадкам» (компания / найдено / kept / rejected / топ-причина). Для разовых полных прогонов используйте `--limit 0` (без лимита) или `--limit 198` для всех целей в `targets.yaml`.

## 7. Обогащение и скоринг только «свежих» вакансий

`run_enrich` и `run_score` поддерживают `--since YYYY-MM-DD` (UTC, начало дня). **По умолчанию** обрабатываются только строки с `created_at` от **сегодняшнего дня UTC**, чтобы не задевать старые записи.

Примеры:

```bash
docker compose exec api python -m backend.pipeline.run_enrich --batch 50
docker compose exec api python -m backend.pipeline.run_score --batch 50
docker compose exec api python -m backend.pipeline.run_enrich --since 2026-01-01 --batch 200
```

## 8. Полный прогон всех tier и systemd (без автозапуска по умолчанию)

Разовый полный прогон (из каталога `infra/`, контейнер `api` должен быть запущен):

```bash
docker compose exec -T api python -m backend.pipeline.run_crawl --tier 1 --limit 0
docker compose exec -T api python -m backend.pipeline.run_crawl --tier 2 --limit 0
docker compose exec -T api python -m backend.pipeline.run_crawl --tier 3 --limit 0
docker compose exec -T api python -m backend.pipeline.run_crawl --tier 4 --limit 50
docker compose exec -T api python -m backend.pipeline.run_enrich --batch 100
docker compose exec -T api python -m backend.pipeline.run_score --batch 100
docker compose exec -T api python -m backend.pipeline.run_write --batch 20
```

То же через скрипт в репозитории (только вручную / свой cron):

```bash
cd /opt/prometheus-20
chmod +x infra/run_pipeline.sh
bash infra/run_pipeline.sh
```

Для tier 4 можно переопределить лимит: `LIMIT_TIER4=100 bash infra/run_pipeline.sh`.

### Systemd на VPS: таймер в репозитории без реального расписания

Юниты: [`infra/prometheus-pipeline.timer`](../infra/prometheus-pipeline.timer), [`infra/prometheus-pipeline.service`](../infra/prometheus-pipeline.service).

В **`prometheus-pipeline.timer` нет рабочего расписания** (заглушка до 2099 г.), чтобы не уходили деньги на фоновые краулы/LLM. Шаги enrich/normalize/dedup/score/promote — только вручную из UI или `POST /pipeline/step/{name}`.

Если у вас на сервере таймер уже был включён ранее — отключите:

```bash
sudo systemctl disable --now prometheus-pipeline.timer
```

Разовый crawl → stage вручную (после `chmod +x infra/run_crawl_stage.sh` и копирования unit-файлов):

```bash
sudo systemctl start prometheus-pipeline.service
sudo journalctl -u prometheus-pipeline.service -S today --no-pager
```

Чтобы снова включить расписание, отредактируйте `OnCalendar` в `prometheus-pipeline.timer`, затем `sudo systemctl daemon-reload` и `sudo systemctl enable --now prometheus-pipeline.timer`.
