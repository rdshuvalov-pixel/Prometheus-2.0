# Pipeline

## Шаги

### 1. Crawl
Источники:
- career pages
- job boards
- ATS (Lever, Greenhouse, Ashby)

### 2. Parse
Извлечь:
- title
- description
- location
- date

### 3. Normalize
LLM + rules:

Output:
{
  role_type,
  seniority,
  work_format,
  location_fit
}

### 4. Dedup
Условие:
company + normalized_title

### 5. Filter

Rules:
- role ∈ Product Manager / Lead / Head
- remote or hybrid Lisbon
- full-time
- date ≤ 5 days

### 6. Score
LLM → structured extraction  
Code → final score

### 7. Write
LLM генерирует:
- formal cover letter
- informal message

### 8. Store
В Supabase

### 9. Report
Сводка + объяснение