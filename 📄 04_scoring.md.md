# Scoring System

## Общий принцип

LLM извлекает признаки  
Code считает score

## Пример факторов

+ Product role
+ Seniority match
+ Remote EU
+ B2B SaaS
+ Fintech / AI
+ Growth / monetisation

## Output LLM

{
  "b2b_saas": true,
  "ai": true,
  "growth": true,
  "confidence": 0.84,
  "evidence": [...]
}

## Code считает

score = sum(weights)

## Диапазоны

80+ → сильные  
70–79 → хорошие  
50–69 → слабые  
<50 → discard