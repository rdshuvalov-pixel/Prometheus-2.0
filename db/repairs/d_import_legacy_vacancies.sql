-- Шаг D: перенос строк из vacancies_legacy → vacancies (схема Prometheus 2.0)
-- Без DROP. Идемпотентность: ON CONFLICT (profile_id, url) DO NOTHING.
--
-- Условия:
--   • Таблица public.vacancies_legacy существует (старое имя public.vacancies).
--   • Уже применены 0001–0007, есть public.vacancies (новая схема) и хотя бы одна строка candidate_profiles (лучше is_default=true).
--   • Расширение uuid-ossp (как в 0001) для uuid_generate_v4().

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'vacancies_legacy'
  ) THEN
    RAISE EXCEPTION 'Ожидается таблица public.vacancies_legacy (переименованная старая vacancies).';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'vacancies'
  ) THEN
    RAISE EXCEPTION 'Ожидается таблица public.vacancies (новая схема из 0003).';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.candidate_profiles LIMIT 1) THEN
    RAISE EXCEPTION 'Таблица candidate_profiles пуста. Сначала выполните в SQL Editor файл db/repairs/ensure_default_profile.sql, либо на VPS: docker compose exec api python -m backend.scripts.seed_profile';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.candidate_profiles WHERE is_default = true) THEN
    RAISE EXCEPTION 'Нужна ровно одна строка candidate_profiles с is_default=true (запустите seed_profile).';
  END IF;
END $$;

WITH prof AS (
  SELECT id AS pid
  FROM public.candidate_profiles
  WHERE is_default = true
  ORDER BY created_at NULLS LAST
  LIMIT 1
),
legacy_url AS (
  SELECT
    l.*,
    COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text) AS canon_url
  FROM public.vacancies_legacy l
)
INSERT INTO public.vacancies (
  id,
  profile_id,
  company,
  role_title,
  role_title_normalized,
  company_normalized,
  url,
  description,
  status,
  score,
  match_status,
  score_breakdown,
  reject_reason,
  warnings,
  evidence,
  normalized_role,
  normalized_seniority,
  normalized_work_format,
  normalized_location,
  employment_type,
  notes,
  enrichment_at,
  scored_at,
  posted_at,
  fetched_at,
  created_at
)
SELECT
  uuid_generate_v4(),
  prof.pid,
  COALESCE(NULLIF(trim(l.company), ''), 'Unknown'),
  COALESCE(NULLIF(trim(l.role_title), ''), 'Unknown'),
  lower(trim(COALESCE(l.role_title, ''))),
  lower(trim(COALESCE(l.company, ''))),
  l.canon_url,
  left(
    trim(
      COALESCE(l.details, '')
      || CASE WHEN COALESCE(l.fit_reasoning, '') <> '' THEN E'\n\n' || l.fit_reasoning ELSE '' END
    ),
    50000
  ),
  CASE
    WHEN lower(coalesce(l.pipeline_status, l.status, '')) ~ '(reject|declin|отказ|ниже порога)' THEN 'Rejected'
    WHEN l.score IS NOT NULL AND l.score >= 50 THEN 'Scored'
    WHEN lower(trim(coalesce(l.applied, ''))) IN ('yes', 'true', 'y', 'applied', 'да') THEN 'Applied'
    WHEN lower(coalesce(l.pipeline_status, l.status, '')) ~ '(interview|интервью)' THEN 'Interview'
    ELSE 'New'
  END::text,
  l.score,
  l.match_status,
  l.score_breakdown,
  NULL::text,
  ARRAY[]::text[],
  jsonb_strip_nulls(
    jsonb_build_object(
      'legacy_id', l.id,
      'platform', l.platform,
      'tier', l.tier,
      'pipeline_status', l.pipeline_status,
      'status', l.status,
      'applied', l.applied,
      'applied_date', l.applied_date,
      'salary_min', l.salary_min,
      'salary_max', l.salary_max,
      'salary_currency', l.salary_currency,
      'is_visa_sponsored', l.is_visa_sponsored,
      'is_relocation', l.is_relocation,
      'cover_informal_present', (trim(coalesce(l.cover_informal, '')) <> ''),
      'cover_formal_present', (trim(coalesce(l.cover_formal, '')) <> '')
    )
  ),
  l.function_norm,
  l.seniority,
  l.work_format,
  l.location_norm,
  NULL::text,
  l.notes,
  l.enriched_at,
  l.scored_at,
  NULL::timestamptz,
  COALESCE(l.enriched_at, l.scored_at, l.created_at::timestamptz, now()),
  COALESCE(l.created_at::timestamptz, now())
FROM legacy_url l
CROSS JOIN prof
WHERE prof.pid IS NOT NULL
ON CONFLICT (profile_id, url) DO NOTHING;

-- Письма: formal / informal в cover_letters (только непустые body)
INSERT INTO public.cover_letters (vacancy_id, kind, body, model)
SELECT v.id, 'formal', trim(l.cover_formal), 'legacy-import'
FROM public.vacancies_legacy l
CROSS JOIN (SELECT id AS pid FROM public.candidate_profiles WHERE is_default = true LIMIT 1) d
JOIN public.vacancies v
  ON v.profile_id = d.pid
 AND v.url = COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text)
WHERE trim(coalesce(l.cover_formal, '')) <> ''
ON CONFLICT (vacancy_id, kind) DO NOTHING;

INSERT INTO public.cover_letters (vacancy_id, kind, body, model)
SELECT v.id, 'informal', trim(l.cover_informal), 'legacy-import'
FROM public.vacancies_legacy l
CROSS JOIN (SELECT id AS pid FROM public.candidate_profiles WHERE is_default = true LIMIT 1) d
JOIN public.vacancies v
  ON v.profile_id = d.pid
 AND v.url = COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text)
WHERE trim(coalesce(l.cover_informal, '')) <> ''
ON CONFLICT (vacancy_id, kind) DO NOTHING;

-- Источник для трассировки (без дубликатов при повторном запуске)
INSERT INTO public.vacancy_sources (vacancy_id, source_url, tier, ats_type)
SELECT v.id, COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text), l.tier, l.platform
FROM public.vacancies_legacy l
CROSS JOIN (SELECT id AS pid FROM public.candidate_profiles WHERE is_default = true LIMIT 1) d
JOIN public.vacancies v
  ON v.profile_id = d.pid
 AND v.url = COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text)
WHERE NOT EXISTS (
  SELECT 1 FROM public.vacancy_sources vs
  WHERE vs.vacancy_id = v.id
    AND vs.source_url = COALESCE(NULLIF(trim(l.url), ''), 'legacy://' || l.id::text)
);

COMMIT;
