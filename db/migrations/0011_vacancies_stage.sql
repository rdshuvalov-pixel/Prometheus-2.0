CREATE TABLE IF NOT EXISTS vacancies_stage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES candidate_profiles (id) ON DELETE CASCADE,
  run_id UUID REFERENCES pipeline_runs (id) ON DELETE SET NULL,
  source TEXT,
  url TEXT NOT NULL,
  company TEXT NOT NULL,
  role_title TEXT NOT NULL,
  description TEXT DEFAULT '',
  posted_at TIMESTAMPTZ,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_payload JSONB,
  content_hash TEXT,
  company_normalized TEXT DEFAULT '',
  role_title_normalized TEXT DEFAULT '',
  dedup_key TEXT,
  dedup_status TEXT,
  score INT,
  status TEXT NOT NULL DEFAULT 'Staged'
    CHECK (status IN ('Staged', 'DedupKept', 'DedupDropped', 'ScoredSelected', 'ScoredRejected', 'Promoted')),
  reject_reason TEXT REFERENCES reject_reasons (code),
  warnings TEXT[] DEFAULT ARRAY[]::TEXT[],
  evidence JSONB,
  score_breakdown JSONB,
  promoted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (profile_id, url)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_run_created
  ON vacancies_stage (profile_id, run_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vacancies_stage_profile_status_created
  ON vacancies_stage (profile_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_vacancies_stage_dedup_key
  ON vacancies_stage (profile_id, dedup_key);

