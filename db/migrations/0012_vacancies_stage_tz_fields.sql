-- TЗ: enrich full page text + LLM normalization + dedup vs master + score outputs.
-- This migration extends `vacancies_stage` without breaking existing stepwise pipeline.

ALTER TABLE vacancies_stage
  -- Stage-1 (fast crawl) fields from spec
  ADD COLUMN IF NOT EXISTS platform TEXT,
  ADD COLUMN IF NOT EXISTS company_name TEXT,
  ADD COLUMN IF NOT EXISTS job_title TEXT,
  ADD COLUMN IF NOT EXISTS job_url TEXT,
  ADD COLUMN IF NOT EXISTS location_raw TEXT,
  ADD COLUMN IF NOT EXISTS role_match TEXT,
  ADD COLUMN IF NOT EXISTS pipeline_status TEXT,

  -- Stage-2 enrich: full page + blocks
  ADD COLUMN IF NOT EXISTS page_text_full TEXT,
  ADD COLUMN IF NOT EXISTS page_text_header TEXT,
  ADD COLUMN IF NOT EXISTS page_text_sidebar TEXT,
  ADD COLUMN IF NOT EXISTS page_text_extra JSONB,

  -- Stage-3 LLM normalize: structured payload + key extracted columns
  ADD COLUMN IF NOT EXISTS normalized_payload JSONB,
  ADD COLUMN IF NOT EXISTS normalized_title TEXT,
  ADD COLUMN IF NOT EXISTS seniority TEXT,
  ADD COLUMN IF NOT EXISTS function TEXT,
  ADD COLUMN IF NOT EXISTS domain TEXT,
  ADD COLUMN IF NOT EXISTS industry TEXT,
  ADD COLUMN IF NOT EXISTS employment_type TEXT,
  ADD COLUMN IF NOT EXISTS work_format TEXT,
  ADD COLUMN IF NOT EXISTS location_normalized TEXT,
  ADD COLUMN IF NOT EXISTS country TEXT,
  ADD COLUMN IF NOT EXISTS remote_allowed BOOLEAN,
  ADD COLUMN IF NOT EXISTS hybrid_allowed BOOLEAN,
  ADD COLUMN IF NOT EXISTS relocation_required BOOLEAN,
  ADD COLUMN IF NOT EXISTS salary_min INT,
  ADD COLUMN IF NOT EXISTS salary_max INT,
  ADD COLUMN IF NOT EXISTS salary_currency TEXT,
  ADD COLUMN IF NOT EXISTS english_required BOOLEAN,
  ADD COLUMN IF NOT EXISTS product_type TEXT,
  ADD COLUMN IF NOT EXISTS b2b_or_b2c TEXT,
  ADD COLUMN IF NOT EXISTS ai_related BOOLEAN,
  ADD COLUMN IF NOT EXISTS fintech_related BOOLEAN,
  ADD COLUMN IF NOT EXISTS growth_related BOOLEAN,
  ADD COLUMN IF NOT EXISTS monetization_related BOOLEAN,
  ADD COLUMN IF NOT EXISTS platform_related BOOLEAN,
  ADD COLUMN IF NOT EXISTS technical_depth TEXT,
  ADD COLUMN IF NOT EXISTS management_scope TEXT,
  ADD COLUMN IF NOT EXISTS must_have_requirements TEXT[],
  ADD COLUMN IF NOT EXISTS nice_to_have_requirements TEXT[],
  ADD COLUMN IF NOT EXISTS responsibilities TEXT[],
  ADD COLUMN IF NOT EXISTS red_flags TEXT[],
  ADD COLUMN IF NOT EXISTS positive_signals TEXT[],
  ADD COLUMN IF NOT EXISTS normalization_confidence REAL,

  -- Stage-4 dedup vs master
  ADD COLUMN IF NOT EXISTS duplicate_of_id UUID REFERENCES vacancies (id),
  ADD COLUMN IF NOT EXISTS duplicate_reason TEXT,

  -- Stage-5 score outputs from spec
  ADD COLUMN IF NOT EXISTS score_summary TEXT,
  ADD COLUMN IF NOT EXISTS score_positive_factors TEXT[],
  ADD COLUMN IF NOT EXISTS score_negative_factors TEXT[],
  ADD COLUMN IF NOT EXISTS score_risks TEXT[],
  ADD COLUMN IF NOT EXISTS score_confidence REAL,

  -- Stage-6 promote bookkeeping
  ADD COLUMN IF NOT EXISTS master_table_id UUID REFERENCES vacancies (id),
  ADD COLUMN IF NOT EXISTS added_to_master_at TIMESTAMPTZ;

-- Backfill compatibility aliases for existing rows (best-effort).
UPDATE vacancies_stage
SET
  company_name = COALESCE(company_name, company),
  job_title = COALESCE(job_title, role_title),
  job_url = COALESCE(job_url, url)
WHERE company_name IS NULL OR job_title IS NULL OR job_url IS NULL;

CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_pipeline_status_created
  ON vacancies_stage (profile_id, pipeline_status, created_at);
CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_duplicate_of
  ON vacancies_stage (profile_id, duplicate_of_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_master_table_id
  ON vacancies_stage (profile_id, master_table_id);

