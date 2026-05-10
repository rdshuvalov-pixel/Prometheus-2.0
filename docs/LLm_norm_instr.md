# Job Aggregation & Deduplication Architecture

---

## Mapping to Prometheus 2.0

Этот файл описывает общую трёхслойную модель. В **Prometheus 2.0** соответствие такое:

| Концепция здесь | Реализация в проекте |
|-----------------|----------------------|
| `raw_jobs` | Строки **`vacancies_stage`** после crawl / enrich (`url`, `page_text_full`, `description`, метаданные). |
| LLM normalization | Скрипт **`backend/pipeline/run_llm_normalize_stage.py`**, контракт промпта — **[docs/llm_prompt.md](./llm_prompt.md)**. |
| Нормализованный слой (`normalized_jobs`) | Те же строки **`vacancies_stage`** после LLM: `normalized_payload`, колонки `normalized_*`, `job_fingerprint`, `llm_model`, `prompt_version`. |
| Целевой слой (`target_jobs`) | Таблица **`vacancies`** после **`run_promote`**; связи — `master_table_id`, дедуп на stage — `duplicate_of_id`. |

Источник правды по полям JSON, enums, fingerprint и версии промпта: **[docs/llm_prompt.md](./llm_prompt.md)**.

---

## Goal

Build a scalable pipeline for collecting, normalizing, filtering, and deduplicating job vacancies from multiple sources.

The system must:
- avoid reprocessing identical vacancies;
- avoid storing duplicate “meaning-equivalent” jobs;
- preserve all discovered source URLs;
- separate raw scraped data from normalized structured entities;
- minimize LLM costs.

---

# High-Level Pipeline

```text
Crawler
    ↓
raw_jobs
    ↓
LLM normalization
    ↓
normalized_jobs
    ↓
filtering / scoring / matching
    ↓
target_jobs (canonical vacancies)
```

---

# 1. raw_jobs

## Purpose

Store everything discovered by the crawler before normalization.

This layer represents:
- raw pages;
- raw text;
- raw metadata;
- source URLs.

No business logic here.

---

## Main Responsibilities

- collect vacancies;
- normalize URLs;
- remove obvious duplicates;
- preserve original text;
- avoid repeated LLM calls.

---

## Recommended Fields

```sql
id uuid primary key

source_platform text
source_url text
canonical_url text

company_raw text
title_raw text
location_raw text
employment_raw text
salary_raw text

raw_text text
raw_html_hash text
raw_text_hash text

scraped_at timestamp

parse_status text
parse_error text
```

---

# URL Deduplication

## Purpose

Avoid storing the exact same posting multiple times.

---

## Canonical URL Rules

Remove:
- utm_source
- utm_medium
- utm_campaign
- gh_src
- ref
- tracking params

Example:

```text
https://jobs.lever.co/company/job?utm_source=linkedin
```

becomes:

```text
jobs.lever.co/company/job
```

---

## Constraint

```sql
create unique index raw_jobs_canonical_url_uq
on raw_jobs(canonical_url);
```

---

# Text Deduplication

## Purpose

Avoid reprocessing identical content published under different URLs.

---

## Text Normalization Before Hashing

Recommended preprocessing:

```text
- lowercase
- trim spaces
- collapse repeated whitespace
- remove cookie blocks
- remove legal boilerplate
- remove tracking/footer content
- remove timestamps like:
  "posted 2 days ago"
```

---

## Example Hash Logic

```js
import crypto from 'crypto';

function textHash(text) {
  const normalized = text
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .replace(/posted \d+ days? ago/g, '')
    .trim();

  return crypto
    .createHash('sha256')
    .update(normalized)
    .digest('hex');
}
```

---

## Index

```sql
create unique index raw_jobs_text_hash_uq
on raw_jobs(raw_text_hash);
```

---

# 2. normalized_jobs

## Purpose

Store structured job information extracted via LLM.

This layer converts:
- raw text
→ structured attributes.

---

# LLM Responsibilities

The LLM should:
- normalize titles;
- infer seniority;
- infer function/domain;
- classify work format;
- extract salary;
- identify AI/fintech/growth relevance;
- identify responsibilities and requirements.

---

# Recommended Flow

```text
1. Select raw_jobs where normalization_status = pending
2. Build compact JSON payload
3. Send payload to LLM
4. Validate response
5. Store normalized fields
6. Generate fingerprint
7. Mark normalization complete
```

---

# Recommended Additional Fields

```sql
normalization_status text
normalization_error text

normalization_model text
normalization_prompt_version text

normalized_at timestamp
```

---

# Example Normalized Fields

```sql
normalized_title text
seniority text
function text
domain text
industry text

employment_type text
work_format text

location_normalized text
country text

remote_allowed boolean
hybrid_allowed boolean

salary_min int
salary_max int
salary_currency text

ai_related boolean
fintech_related boolean
growth_related boolean
monetization_related boolean
platform_related boolean

technical_depth text
management_scope text

must_have_requirements jsonb
nice_to_have_requirements jsonb
responsibilities jsonb

red_flags jsonb
positive_signals jsonb

normalization_confidence float
```

---

# Semantic Deduplication

## Problem

The same vacancy may appear:
- on Lever;
- on LinkedIn;
- on company careers page;
- on Greenhouse;
- under slightly different URLs or wording.

URL dedupe is not enough.

---

# Canonical Job Fingerprint

Generate a semantic identity key.

---

## Recommended Fingerprint Components

```text
company_normalized
normalized_title
seniority
function
country
location_normalized
```

---

## Example

```text
bumble|senior product manager|senior|product management|uk|london
```

---

## Example Hash

```js
function fingerprintHash(job) {
  const value = [
    job.company,
    job.normalized_title,
    job.location_normalized,
    job.country,
    job.seniority,
    job.function,
  ]
    .map(v => (v || '').toLowerCase().trim())
    .join('|');

  return crypto
    .createHash('sha256')
    .update(value)
    .digest('hex');
}
```

---

# Important Recommendation

DO NOT make fingerprint unique initially.

Two jobs may:
- look extremely similar;
- belong to different teams;
- be reopened;
- represent separate headcount positions.

Instead:
- mark potential duplicates;
- preserve relationships.

---

# Recommended Fields

```sql
job_fingerprint text

dedupe_status text
dedupe_reason text

duplicate_of uuid null

first_seen_at timestamp
last_seen_at timestamp

seen_count int default 1
```

---

# Example Statuses

```text
unique
duplicate_by_url
duplicate_by_text
possible_duplicate
reopened
updated_version
```

---

# 3. target_jobs (Canonical Job Table)

## Purpose

Store high-quality filtered vacancies.

This is the “final” business-facing layer.

---

# Important Concept

Separate:

```text
job_postings
```

from:

```text
jobs
```

---

# Recommended Relationship

```text
1 canonical job
    →
many postings
```

Example:

```text
Canonical Job:
Senior Product Manager at Bumble

Postings:
- Lever URL
- LinkedIn URL
- Company careers URL
```

---

# Recommended Related URLs Structure

```sql
related_urls jsonb
```

Example:

```json
[
  {
    "url": "https://jobs.lever.co/...",
    "source": "lever",
    "seen_at": "2026-05-10"
  },
  {
    "url": "https://linkedin.com/jobs/...",
    "source": "linkedin",
    "seen_at": "2026-05-11"
  }
]
```

---

# Final Deduplication Logic

## Rule Order

### 1. Exact URL match

```text
→ duplicate_by_url
```

Update:
- last_seen_at
- seen_count

Do not create new canonical vacancy.

---

### 2. Exact text hash match

```text
→ duplicate_by_text
```

Do not create new vacancy.

---

### 3. Fingerprint match

```text
→ possible_duplicate
```

Possible actions:
- attach as duplicate_of existing job;
- preserve as separate posting;
- queue for manual review.

---

# Recommended MVP Strategy

## raw_jobs

Use:
- canonical_url
- raw_text_hash

---

## target_jobs

Use:
- canonical_job_key
- duplicate_of
- dedupe_status
- related_urls

---

# Recommended Principle

Never physically delete duplicates.

Instead:
- preserve history;
- preserve sources;
- maintain canonical relationships.

---

# Practical Summary

## raw_jobs

Represents:
- raw discovered postings.

Deduplication:
- URL;
- text hash.

---

## normalized_jobs

Represents:
- structured interpretation.

Deduplication:
- semantic fingerprint.

---

## target_jobs

Represents:
- business-quality canonical vacancies.

Deduplication:
- meaning-based canonicalization;
- related postings;
- source preservation.

---

# Recommended Engineering Principle

Crawler should:
- collect;
- normalize URLs;
- store raw data.

LLM should:
- interpret;
- classify;
- normalize.

Business logic should:
- score;
- deduplicate;
- rank.

Do not mix all responsibilities into one pipeline stage.
Otherwise debugging becomes archaeology.