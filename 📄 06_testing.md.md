# Testing

## 1. Unit tests (без LLM)
- фильтры
- дедуп
- даты
- локации

## 2. Golden dataset

100–300 вакансий

{
  expected_role,
  expected_score_range,
  expected_decision
}

## 3. Schema validation

LLM output должен соответствовать JSON schema

## 4. Human review

Если:
- confidence < 0.75
- ambiguous location

→ manual check