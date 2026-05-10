"""Markers for crawl → post-crawl filter → enrich."""

# Inserted by run_crawl --to-stage (no inline filters).
PIPELINE_CRAWL_RAW = "CrawlRaw"

# Failed post-crawl filters or duplicate vs master vacancies.
PIPELINE_CRAWL_REJECTED = "CrawlRejected"

# After filters pass: ready for enrich_texts (matches historical single-stage crawl).
PIPELINE_AFTER_CRAWL_FILTER = "Staged"
