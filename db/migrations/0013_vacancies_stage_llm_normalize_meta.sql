-- LLM normalization metadata, fingerprint, optional input size (docs/llm_prompt.md §10, §14–16).

ALTER TABLE vacancies_stage
  ADD COLUMN IF NOT EXISTS job_fingerprint TEXT,
  ADD COLUMN IF NOT EXISTS llm_model TEXT,
  ADD COLUMN IF NOT EXISTS prompt_version TEXT,
  ADD COLUMN IF NOT EXISTS normalized_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS input_char_count INT;

CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_job_fingerprint
  ON vacancies_stage (profile_id, job_fingerprint)
  WHERE job_fingerprint IS NOT NULL AND job_fingerprint <> '';
