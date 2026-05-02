# Ремонт и перенос данных

## `ensure_default_profile.sql`

Если **`candidate_profiles` пуста** (ошибка при импорте): выполните этот файл в SQL Editor **до** `d_import_legacy_vacancies.sql`. Альтернатива — на VPS: `docker compose exec api python -m backend.scripts.seed_profile`.

## `d_import_legacy_vacancies.sql` (шаг D)

Перенос из `vacancies_legacy` (старая таблица после `ALTER RENAME`) в новую `public.vacancies` + заполнение `cover_letters` и `vacancy_sources`.

**Порядок:**

1. Миграции `0001`–`0007` применены, новая `vacancies` существует.
2. `ALTER TABLE public.vacancies RENAME TO vacancies_legacy` уже выполнен (старые данные в `vacancies_legacy`).
3. В `candidate_profiles` есть хотя бы одна строка с **`is_default = true`** (`ensure_default_profile.sql` или `seed_profile`).

**Запуск:** в Supabase **SQL Editor** вставьте целиком содержимое `d_import_legacy_vacancies.sql` и выполните.

Повторный запуск: строки с тем же `(profile_id, url)` пропускаются (`ON CONFLICT DO NOTHING`).
