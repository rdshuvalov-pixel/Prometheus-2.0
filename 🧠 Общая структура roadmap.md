Phase 0 — Foundation
Phase 1 — Data Pipeline (core)
Phase 2 — LLM Integration
Phase 3 — Scoring & Decisions
Phase 4 — Output (Letters + DB)
Phase 5 — Transparency & UI
Phase 6 — QA & Testing
Phase 7 — Iteration & Scaling

# **📍 Phase 0 — Foundation**

## **🎯 Goal**

Подготовить инфраструктуру

## **Tasks**

### **0.1 Repo setup**

- создать repo
- структура проекта
- env config (OpenRouter, Supabase)

### **0.2 Supabase setup**

- таблицы:
    - vacancies
    - pipeline_runs
    - pipeline_events
    - llm_calls
- индексы (company + role_title)

### **0.3 LLM Gateway (MVP)**

- базовый wrapper
- retry
- logging
- model routing

📌 Deliverable:  
→ можно дергать LLM через единый интерфейс

---

# **📍 Phase 1 — Data Pipeline (core)**

## **🎯 Goal**

Собирать вакансии

## **Tasks**

### **1.1 Crawler (ATS first)**

- Lever parser
- Greenhouse parser
- Ashby parser

### **1.2 Raw ingestion**

- сохранять:
    - title
    - company
    - description
    - location
    - date
    - url

### **1.3 Normalization (rules only)**

- role detection (regex)
- seniority extraction
- location parsing
- date parsing

### **1.4 Dedup engine**

- ключ: company + normalized_title
- fuzzy match (optional)

📌 Deliverable:  
→ raw pipeline работает без LLM

---

# **📍 Phase 2 — LLM Integration**

## **🎯 Goal**

Добавить интеллект

## **Tasks**

### **2.1 classify_location()**

- remote / hybrid / office
- EU compatible или нет
- confidence + evidence

### **2.2 extract_role_semantics()**

- Product vs non-product
- domain (AI / fintech / SaaS)

### **2.3 JSON schema validation**

- enforce structure
- reject invalid output

### **2.4 fallback logic**

- retry с другой моделью

📌 Deliverable:  
→ LLM даёт структурированные данные

---

# **📍 Phase 3 — Scoring & Decisions**

## **🎯 Goal**

Понимать “насколько это хорошая вакансия”

## **Tasks**

### **3.1 Feature extraction (LLM)**

- b2b_saas
- fintech
- ai
- growth
- seniority_fit
- remote_fit

### **3.2 Score engine (code)**

- weights
- итоговый score

### **3.3 Decision logic**

- score ≥50 → keep
- score <50 → reject

### **3.4 Explanation generator**

- why kept
- risks
- evidence

📌 Deliverable:  
→ каждая вакансия имеет score + объяснение

---

# **📍 Phase 4 — Output (Letters + DB)**

## **🎯 Goal**

Готовить отклики

## **Tasks**

### **4.1 Cover letter generator**

- formal
- informal
- шаблоны + CV

### **4.2 Supabase integration**

- insert vacancy
- статус: Scored

### **4.3 Status system**

- New
- Scored
- Applied
- Interview

📌 Deliverable:  
→ готовые вакансии + письма

---

# **📍 Phase 5 — Transparency & UI**

## **🎯 Goal**

Пользователь понимает, что происходит

## **Tasks**

### **5.1 Pipeline events**

- crawl started
- parsing done
- filtering done
- scoring done

### **5.2 Metrics**

- found
- rejected
- duplicates
- kept

### **5.3 Vacancy explanation UI**

- score
- why
- risks

### **5.4 Timeline view**

- события по времени

📌 Deliverable:  
→ прозрачный pipeline

---

# **📍 Phase 6 — QA & Testing**

## **🎯 Goal**

Стабильность

## **Tasks**

### **6.1 Unit tests**

- filters
- dedup
- date parsing

### **6.2 Golden dataset**

- 100+ вакансий
- expected outputs

### **6.3 LLM validation**

- schema check
- fallback

### **6.4 Edge cases**

- unknown date
- weird location

📌 Deliverable:  
→ система не разваливается

---

# **📍 Phase 7 — Iteration & Scaling**

## **🎯 Goal**

Улучшать

## **Tasks**

### **7.1 Model tuning**

- cheap vs strong routing

### **7.2 Source expansion**

- новые сайты

### **7.3 Performance**

- async pipeline
- batching

### **7.4 Cost control**

- LLM usage tracking

📌 Deliverable:  
→ scalable система

---

# **🧩 Linear структура (как эпики)**
EPIC 1 — Infrastructure
EPIC 2 — Data Pipeline
EPIC 3 — LLM Layer
EPIC 4 — Scoring System
EPIC 5 — Output Generation
EPIC 6 — Transparency UI
EPIC 7 — QA & Reliability
EPIC 8 — Scaling

