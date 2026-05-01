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

Cheap model:
- extraction
- classification

Strong model:
- scoring explanation
- writing

## Запрещено

- LLM считает финальный score
- LLM пишет в БД напрямую