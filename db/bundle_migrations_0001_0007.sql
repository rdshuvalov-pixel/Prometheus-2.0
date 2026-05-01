-- Прометей 2.0: bundle 0001–0007 (выполнить в Supabase SQL Editor или через apply_migrations.py)

-- FILE: 0001_lookup_enums.sql
-- Lookup tables for canonical reject reasons and warnings (prometei_filter_model §20–21)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS reject_reasons (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warnings (
  code TEXT PRIMARY KEY,
  label TEXT NOT NULL
);

INSERT INTO reject_reasons (code, label) VALUES
  ('not_product_role', 'Не продуктовая роль'),
  ('project_manager_only', 'Только Project Manager без product ownership'),
  ('marketing_role', 'Marketing'),
  ('operations_role', 'Operations'),
  ('business_analyst_no_product', 'BA без продуктовой ответственности'),
  ('office_only', 'Только офис'),
  ('hybrid_outside_lisbon', 'Hybrid не в Лиссабоне'),
  ('us_only', 'Только США'),
  ('uk_only_without_work_rights', 'UK без права работы'),
  ('expired_or_old', 'Устарела / >5 дней'),
  ('part_time', 'Не full-time'),
  ('internship', 'Стажировка'),
  ('duplicate', 'Дубликат'),
  ('insufficient_data', 'Недостаточно данных'),
  ('low_salary', 'Низкая компенсация'),
  ('domain_mismatch', 'Домен не подходит'),
  ('below_threshold', 'Ниже порога скоринга (<50)'),
  ('search_role_excluded', 'Исключено на этапе поиска по роли')
ON CONFLICT (code) DO NOTHING;

INSERT INTO warnings (code, label) VALUES
  ('date_unknown', 'Дата публикации неизвестна'),
  ('employment_type_unknown', 'Тип занятости не указан'),
  ('salary_unknown', 'Зарплата не указана'),
  ('location_ambiguous', 'Локация неоднозначна'),
  ('remote_policy_ambiguous', 'Remote-политика неясна'),
  ('short_description', 'Короткое описание JD'),
  ('domain_risk', 'Риск домена'),
  ('seniority_too_high', 'Грейд выше профиля'),
  ('seniority_too_low', 'Грейд ниже профиля'),
  ('requires_travel', 'Требуются поездки'),
  ('requires_local_language', 'Локальный язык обязателен')
ON CONFLICT (code) DO NOTHING;

-- FILE: 0002_candidate_profiles.sql
CREATE TABLE IF NOT EXISTS candidate_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID,
  name TEXT NOT NULL DEFAULT 'Ruslan Shuvalov',
  profession TEXT NOT NULL DEFAULT 'Product Manager',
  search_keywords TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  resume_md TEXT DEFAULT '',
  interview_md TEXT DEFAULT '',
  work_history_md TEXT DEFAULT '',
  scoring_overrides JSONB DEFAULT NULL,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidate_profiles_default ON candidate_profiles (is_default);

-- FILE: 0003_vacancies.sql
CREATE TABLE IF NOT EXISTS vacancies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES candidate_profiles (id) ON DELETE CASCADE,
  company TEXT NOT NULL,
  role_title TEXT NOT NULL,
  role_title_normalized TEXT NOT NULL DEFAULT '',
  company_normalized TEXT NOT NULL DEFAULT '',
  url TEXT NOT NULL,
  description TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'New'
    CHECK (status IN ('New', 'Scored', 'Rejected', 'Applied', 'Interview')),
  score INT,
  match_status TEXT,
  score_breakdown JSONB,
  reject_reason TEXT REFERENCES reject_reasons (code),
  warnings TEXT[] DEFAULT ARRAY[]::TEXT[],
  evidence JSONB,
  normalized_role TEXT,
  normalized_seniority TEXT,
  normalized_work_format TEXT,
  normalized_location TEXT,
  employment_type TEXT,
  notes TEXT,
  previous_vacancy_id UUID REFERENCES vacancies (id),
  enrichment_at TIMESTAMPTZ,
  scored_at TIMESTAMPTZ,
  why_kept TEXT[],
  risks TEXT[],
  posted_at TIMESTAMPTZ,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (profile_id, url)
);

CREATE TABLE IF NOT EXISTS vacancy_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  vacancy_id UUID NOT NULL REFERENCES vacancies (id) ON DELETE CASCADE,
  source_url TEXT NOT NULL,
  tier TEXT,
  ats_type TEXT
);

CREATE INDEX IF NOT EXISTS idx_vacancies_profile_status ON vacancies (profile_id, status);
CREATE INDEX IF NOT EXISTS idx_vacancies_company_role ON vacancies (company_normalized, role_title_normalized);
CREATE INDEX IF NOT EXISTS idx_vacancies_score ON vacancies (score);

-- FILE: 0004_audit_llm.sql
CREATE TABLE IF NOT EXISTS raw_vacancies (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  payload JSONB NOT NULL,
  source TEXT NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  content_hash TEXT NOT NULL DEFAULT '',
  UNIQUE (source, content_hash)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID REFERENCES candidate_profiles (id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running',
  metrics JSONB DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS pipeline_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES pipeline_runs (id) ON DELETE CASCADE,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  level TEXT NOT NULL DEFAULT 'info',
  type TEXT NOT NULL,
  payload JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_run ON pipeline_events (run_id, ts DESC);

CREATE TABLE IF NOT EXISTS llm_calls (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id UUID REFERENCES pipeline_runs (id) ON DELETE SET NULL,
  vacancy_id UUID REFERENCES vacancies (id) ON DELETE SET NULL,
  function TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt TEXT,
  response TEXT,
  tokens_in INT,
  tokens_out INT,
  cost NUMERIC(12, 6),
  latency_ms INT,
  status TEXT NOT NULL DEFAULT 'ok'
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_run ON llm_calls (run_id);

-- FILE: 0005_cover_letters.sql
CREATE TABLE IF NOT EXISTS cover_letters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  vacancy_id UUID NOT NULL REFERENCES vacancies (id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('formal', 'informal')),
  body TEXT NOT NULL,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (vacancy_id, kind)
);

-- FILE: 0006_rls.sql
-- RLS: включить после создания пользователя в Supabase Auth.
-- Анонимный доступ закрыт; authenticated читают свои данные.

ALTER TABLE candidate_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE vacancies ENABLE ROW LEVEL SECURITY;
ALTER TABLE vacancy_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE cover_letters ENABLE ROW LEVEL SECURITY;

-- Политики-примеры (уточните user_id в профилях после первого логина):

CREATE POLICY "profiles_select_own" ON candidate_profiles
  FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "profiles_update_own" ON candidate_profiles
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "vacancies_select_authenticated" ON vacancies
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "pipeline_select_authenticated" ON pipeline_runs
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "events_select_authenticated" ON pipeline_events
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "letters_select_authenticated" ON cover_letters
  FOR SELECT TO authenticated USING (true);

-- FILE: 0007_llm_cache_and_alerts.sql
CREATE TABLE IF NOT EXISTS llm_response_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  url TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  function_name TEXT NOT NULL,
  response_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (url, content_hash, function_name)
);

CREATE TABLE IF NOT EXISTS crawl_company_failures (
  company_normalized TEXT NOT NULL,
  fail_count INT NOT NULL DEFAULT 0,
  last_failed_at TIMESTAMPTZ,
  disabled BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (company_normalized)
);
