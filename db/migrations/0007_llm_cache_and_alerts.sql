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
