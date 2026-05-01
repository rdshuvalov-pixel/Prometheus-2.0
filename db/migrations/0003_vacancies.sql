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
