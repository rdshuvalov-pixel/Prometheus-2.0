-- Legacy rows: pipeline_status was NULL before crawl/raw split; treat as already filtered (ready for enrich).
UPDATE vacancies_stage
SET pipeline_status = 'Staged'
WHERE pipeline_status IS NULL;
