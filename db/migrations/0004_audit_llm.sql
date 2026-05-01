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
