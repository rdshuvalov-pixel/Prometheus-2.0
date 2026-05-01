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
