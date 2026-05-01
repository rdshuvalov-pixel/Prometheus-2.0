# Architecture

## High-level

Backend Orchestrator управляет пайплайном:

crawl → parse → normalize → dedup → filter → score → write → store

## Компоненты

### 1. Crawler
- обход сайтов
- сбор raw HTML / JSON

### 2. Parser
- извлечение:
  - title
  - company
  - description
  - location
  - date

### 3. Normalizer
- приводит к стандарту:
  - role_type
  - seniority
  - work_format
  - location_fit

### 4. Dedup Engine
- уникальность:
  - company + role_title

### 5. Rule Filter
- жесткие правила (без LLM)

### 6. LLM Gateway
- все вызовы моделей

### 7. Scoring Engine
- считает score на основе структуры

### 8. Writer
- генерирует cover letters

### 9. Storage (Supabase)

### 10. Dashboard
- показывает процесс

## Главный принцип

Pipeline deterministic  
LLM stateless