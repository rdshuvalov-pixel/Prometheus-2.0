CREATE TABLE IF NOT EXISTS cover_letters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  vacancy_id UUID NOT NULL REFERENCES vacancies (id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('formal', 'informal')),
  body TEXT NOT NULL,
  model TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (vacancy_id, kind)
);
