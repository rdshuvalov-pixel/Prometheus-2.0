# LLM Design

## Подход

Не агенты, а функции:

- extract_job()
- classify_location()
- score_match()
- write_cover_letter()

## Контракт

Каждый вызов:

Input → JSON  
Output → строго JSON  

## Пример

{
  "role_type": "Product Manager",
  "confidence": 0.92,
  "evidence": ["Senior PM", "product ownership"]
}

Если нет evidence → reject

## LLM Gateway

Функции:

- routing моделей
- retry
- fallback
- validation

## Модели

Cheap model: `qwen/qwen3.5-flash-02-23`
- `classify_location`
- `extract_role_semantics`
- `extract_scoring_features`

Strong model: `qwen/qwen3.5-35b-a3b`
- `explain_fit`
- writing (formal cover letter)
- fallback при ошибке парсинга/валидации
- повтор при `confidence < 0.6`

Прайсы (USD за 1M токенов, основной тариф OpenRouter) задаются в [backend/llm/models.yaml](backend/llm/models.yaml) → блок `prices`. Cost попадает в `llm_calls.cost` (см. [backend/llm/gateway.py](backend/llm/gateway.py)).

## Запрещено

- LLM считает финальный score
- LLM пишет в БД напрямую