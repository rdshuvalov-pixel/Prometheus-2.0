-- Если candidate_profiles пуста — одна строка с тем же UUID, что даёт seed_profile
-- (uuid v5: namespace 6ba7b810-9dad-11d1-80b4-00c04fd430c8, имя "Ruslan Shuvalov").
-- Выполни в SQL Editor ПЕРЕМ d_import_legacy_vacancies.sql, если видишь ошибку про отсутствие профиля.

INSERT INTO public.candidate_profiles (
  id,
  name,
  profession,
  search_keywords,
  resume_md,
  interview_md,
  work_history_md,
  scoring_overrides,
  is_default
)
SELECT
  uuid_generate_v5('6ba7b810-9dad-11d1-80b4-00c04fd430c8'::uuid, 'Ruslan Shuvalov'),
  'Ruslan Shuvalov',
  'Senior Product Manager',
  ARRAY['Product Manager', 'Senior Product Manager']::text[],
  '',
  '',
  '',
  NULL::jsonb,
  true
WHERE NOT EXISTS (SELECT 1 FROM public.candidate_profiles LIMIT 1);
