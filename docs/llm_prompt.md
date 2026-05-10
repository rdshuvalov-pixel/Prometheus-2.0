# LLM Normalization Script Specification

## Goal

The script takes raw job descriptions from the database, sends a compact structured request to an LLM, receives normalized JSON, validates it, and writes the result back to the database.

The goal is to make job analysis:
- cheap;
- fast;
- repeatable;
- easy to debug;
- protected from duplicate processing.

---

# Pipeline

```text
raw_jobs
  ↓
select pending records
  ↓
build compact LLM payload
  ↓
send to LLM
  ↓
receive strict JSON
  ↓
validate response
  ↓
write normalized result
  ↓
mark record as done / failed
```

---

# 1. What the Script Takes From DB

The LLM script should not scrape pages.  
Crawler already did that.

The script reads from `raw_jobs`.

## Required Input Fields

```sql
id
source_url
canonical_url
source_platform

company_raw
title_raw
location_raw
department_raw
employment_raw
salary_raw

raw_text
raw_text_hash

scraped_at
```

## Optional Input Fields

```sql
country_raw
remote_raw
html_title
meta_description
page_header
```

---

# 2. Which Records to Process

The script should process only records that are not normalized yet.

Example:

```sql
select *
from raw_jobs
where normalization_status is null
   or normalization_status = 'pending'
limit 20;
```

Alternative:

```sql
select *
from raw_jobs
where normalized_at is null
  and parse_status = 'success'
limit 20;
```

Recommended batch size for MVP:

```text
10-20 jobs per run
```

Do not start with 500 unless the goal is to burn API money for sport.

---

# 3. What to Send to LLM

Do not send raw HTML.

Send a compact JSON payload.

## Recommended Payload

```json
{
  "raw_job_id": "uuid",
  "source_url": "https://jobs.lever.co/company/job-id",
  "source_platform": "lever",
  "company_raw": "Bumble Inc.",
  "title_raw": "Senior Product Manager, Growth",
  "location_raw": "London, UK",
  "department_raw": "Product",
  "employment_raw": "Full-time",
  "salary_raw": null,
  "raw_text": "Full cleaned job description text..."
}
```

---

# 4. Text Size Control

## Recommended Limit

Send no more than:

```text
12,000-16,000 characters
```

for one vacancy.

This is usually enough for:
- title;
- location;
- company;
- role description;
- responsibilities;
- requirements;
- benefits;
- salary if present.

---

## If raw_text Is Too Long

Do not blindly truncate from the end.

Build a compact text from prioritized sections:

```text
1. Header / title / location / employment
2. First part of job description
3. Responsibilities section
4. Requirements section
5. Compensation / salary section
6. Remote / hybrid / location section
7. Benefits section
```

---

# 5. Compact Text Builder

## Recommended Logic

```js
function buildJobTextForLLM(job) {
  const parts = [];

  parts.push(`Company: ${job.company_raw || ''}`);
  parts.push(`Raw title: ${job.title_raw || ''}`);
  parts.push(`Raw location: ${job.location_raw || ''}`);
  parts.push(`Raw department: ${job.department_raw || ''}`);
  parts.push(`Raw employment: ${job.employment_raw || ''}`);
  parts.push(`Raw salary: ${job.salary_raw || ''}`);
  parts.push('');
  parts.push('Job description:');
  parts.push(job.raw_text || '');

  return parts
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .slice(0, 16000);
}
```

This is simple enough for MVP.

Later, improve it by extracting sections before truncation.

---

# 6. LLM Prompt

## System Prompt

```text
You are a job-posting normalization engine.

Your task is to extract structured fields from a job posting.

Return only valid JSON.
Do not include markdown.
Do not include explanations.
Do not include comments.
Use null when a value is not clearly present or cannot be reasonably inferred.
Do not invent salary, location, seniority, remote status, or employment type.
Prefer explicit metadata fields over body text when they conflict.
```

---

## User Prompt

```text
Extract normalized job fields from the following job posting.

Rules:
- normalized_title: clean role title without company, location, remote/hybrid, or employment type.
- seniority: one of Intern, Junior, Middle, Senior, Lead, Principal, Head, Director, VP, C-level, Unknown.
- function: one of Product Management, Product Marketing, Growth, Data, Engineering, Design, Operations, Sales, Marketing, Customer Success, Other, Unknown.
- work_format: one of Remote, Hybrid, Onsite, Flexible, Unknown.
- technical_depth: one of Low, Medium, High, Unknown.
- b2b_or_b2c: one of B2B, B2C, B2B2C, Marketplace, Internal, Unknown.
- salary_min, salary_max, salary_currency must be null unless explicit compensation exists.
- remote_allowed and hybrid_allowed must be null unless explicitly stated or strongly implied.
- english_required should be true if English is explicitly required or the job posting is entirely in English for an international role.
- requirements and responsibilities must be short, deduplicated lists.
- red_flags should describe possible mismatch signals for a senior product / growth / AI / fintech-oriented candidate.
- positive_signals should describe attractive or relevant signals.
- normalization_confidence must be a number from 0 to 1.

Return JSON with exactly this structure:

{
  "normalized_title": null,
  "seniority": null,
  "function": null,
  "domain": null,
  "industry": null,
  "employment_type": null,
  "work_format": null,
  "location_normalized": null,
  "country": null,
  "remote_allowed": null,
  "hybrid_allowed": null,
  "relocation_required": null,
  "salary_min": null,
  "salary_max": null,
  "salary_currency": null,
  "english_required": null,
  "product_type": null,
  "b2b_or_b2c": null,
  "ai_related": null,
  "fintech_related": null,
  "growth_related": null,
  "monetization_related": null,
  "platform_related": null,
  "technical_depth": null,
  "management_scope": null,
  "must_have_requirements": [],
  "nice_to_have_requirements": [],
  "responsibilities": [],
  "red_flags": [],
  "positive_signals": [],
  "normalization_confidence": null
}

Job posting payload:
{{JOB_JSON}}
```

---

# 7. Example LLM Request Payload

The script sends something like this:

```json
{
  "model": "your-model-name",
  "temperature": 0,
  "response_format": {
    "type": "json_object"
  },
  "messages": [
    {
      "role": "system",
      "content": "You are a job-posting normalization engine. Return only valid JSON."
    },
    {
      "role": "user",
      "content": "Extract normalized job fields from this job posting...\n\nJob posting payload:\n{\"raw_job_id\":\"...\",\"source_url\":\"...\",\"company_raw\":\"...\",\"title_raw\":\"...\",\"raw_text\":\"...\"}"
    }
  ]
}
```

Use:

```text
temperature = 0
```

This is extraction, not poetry night.

---

# 8. Expected LLM Response

Example:

```json
{
  "normalized_title": "Senior Product Manager",
  "seniority": "Senior",
  "function": "Product Management",
  "domain": "Growth",
  "industry": "Dating / Social Networking",
  "employment_type": "Full-time",
  "work_format": "Hybrid",
  "location_normalized": "London",
  "country": "United Kingdom",
  "remote_allowed": false,
  "hybrid_allowed": true,
  "relocation_required": null,
  "salary_min": null,
  "salary_max": null,
  "salary_currency": null,
  "english_required": true,
  "product_type": "consumer mobile app",
  "b2b_or_b2c": "B2C",
  "ai_related": false,
  "fintech_related": false,
  "growth_related": true,
  "monetization_related": false,
  "platform_related": false,
  "technical_depth": "Medium",
  "management_scope": "cross-functional leadership",
  "must_have_requirements": [
    "Product management experience",
    "Experience working with cross-functional teams",
    "Strong analytical and prioritization skills"
  ],
  "nice_to_have_requirements": [
    "Experience with consumer mobile products",
    "Experience in growth or engagement"
  ],
  "responsibilities": [
    "Define product strategy and roadmap",
    "Lead discovery and prioritization",
    "Work with engineering, design, and data teams"
  ],
  "red_flags": [
    "Consumer dating/social domain may be less relevant for fintech-focused positioning"
  ],
  "positive_signals": [
    "Senior product ownership",
    "Growth-related scope",
    "Consumer-scale product environment"
  ],
  "normalization_confidence": 0.86
}
```

---

# 9. Response Validation

The script must validate LLM output before writing to DB.

Use:
- Pydantic in Python;
- Zod in TypeScript;
- JSON Schema if language-neutral.

---

## Validation Rules

Required:
- valid JSON;
- all expected keys present;
- no unexpected object structure;
- arrays are arrays;
- booleans are booleans;
- salary values are integers or null;
- confidence is between 0 and 1.

---

## Enum Validation

Validate values for:

```text
seniority
function
work_format
technical_depth
b2b_or_b2c
```

If invalid:
- convert to `Unknown`, or
- mark record as failed.

For MVP, convert to `Unknown` and save warning.

---

# 10. What to Write Back to DB

Write normalized fields into `normalized_jobs` or into normalized columns in `raw_jobs`.

Recommended: separate table.

## normalized_jobs Fields

```sql
id uuid primary key
raw_job_id uuid references raw_jobs(id)

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
relocation_required boolean

salary_min int
salary_max int
salary_currency text

english_required boolean

product_type text
b2b_or_b2c text

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

job_fingerprint text

llm_model text
prompt_version text
normalized_at timestamp
```

---

# 11. Update raw_jobs Status

After success:

```sql
update raw_jobs
set normalization_status = 'done',
    normalized_at = now()
where id = :raw_job_id;
```

After failure:

```sql
update raw_jobs
set normalization_status = 'failed',
    normalization_error = :error_message
where id = :raw_job_id;
```

---

# 12. Failure Handling

## Retryable Errors

Retry:
- LLM timeout;
- rate limit;
- temporary API failure;
- invalid JSON once.

Recommended:

```text
max retries: 2
```

---

## Non-Retryable Errors

Do not retry:
- empty raw_text;
- missing source_url;
- unsupported language if not needed;
- very low-quality page extraction.

---

# 13. Invalid JSON Recovery

If the LLM returns invalid JSON:

1. Retry once with a repair prompt.
2. If still invalid, mark failed.

Repair prompt:

```text
Fix this into valid JSON only. Do not add explanations.

Broken JSON:
{{BROKEN_JSON}}
```

But better: use provider-native JSON mode when available.

---

# 14. Cost Control

## Before Sending to LLM

Skip if:
- `raw_text_hash` already normalized;
- `canonical_url` already normalized;
- raw_text is empty;
- vacancy is already marked duplicate_by_url or duplicate_by_text.

---

## Recommended Controls

Store:

```sql
llm_model
prompt_version
input_char_count
output_char_count
estimated_cost
```

This helps debug why one run suddenly became expensive. Because it will. Software enjoys betrayal.

---

# 15. Prompt Versioning

Store prompt version:

```text
job_normalization_v1
```

When changing prompt rules:

```text
job_normalization_v2
```

This matters because two prompt versions may classify the same role differently.

---

# 16. Fingerprint After Normalization

After receiving normalized fields, generate:

```text
company_normalized
normalized_title
seniority
function
country
location_normalized
```

Then hash it into:

```sql
job_fingerprint
```

Example:

```js
function fingerprintHash(job) {
  const value = [
    job.company_normalized,
    job.normalized_title,
    job.seniority,
    job.function,
    job.country,
    job.location_normalized
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

# 17. Recommended Script Steps

```text
1. Load ENV
2. Connect to DB
3. Select pending raw_jobs
4. For each job:
   4.1 Build compact payload
   4.2 Check text length
   4.3 Send request to LLM
   4.4 Parse JSON
   4.5 Validate schema
   4.6 Generate job_fingerprint
   4.7 Insert into normalized_jobs
   4.8 Update raw_jobs normalization_status = done
   4.9 On error: update raw_jobs normalization_status = failed
5. Log summary
```

---

# 18. Script Output Logs

At the end of each run, log:

```json
{
  "processed": 20,
  "success": 18,
  "failed": 2,
  "skipped_duplicates": 5,
  "model": "model-name",
  "prompt_version": "job_normalization_v1"
}
```

---

# 19. MVP Recommendation

Start with:

```text
batch size: 10
temperature: 0
max raw text: 16000 characters
prompt version: job_normalization_v1
JSON mode: enabled
retry count: 2
```

---

# 20. Key Principle

The LLM script should normalize and classify.

It should not:
- scrape pages;
- decide final business relevance alone;
- overwrite raw data;
- silently discard failed records.

Raw data is evidence.  
Normalized data is interpretation.  
Target table is business decision.