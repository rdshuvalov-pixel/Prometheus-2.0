# Vacancy Scoring Model — Prometei

Версия: 2026-05-01  
Назначение: формализовать модель оценки вакансий Product Manager / Product Lead / Head of Product для Руслана Шувалова.

---

## 1. Назначение модели

Модель нужна, чтобы сравнивать вакансии не “на глаз”, а по единой шкале **0–100**.

Скоринг применяется **после**:
1. сбора вакансии;
2. дедупликации;
3. прохождения первичных фильтров.

LLM может извлекать признаки из описания вакансии, но **финальный балл должен считать код**, а не модель “по ощущению”.

---

## 2. Интерпретация итогового балла

| Балл | Статус | Действие |
|---:|---|---|
| 90–100 | ✅ Отличный мэтч | Показать в отчёте, записать в базу, готовить отклик |
| 70–89 | 🟢 Хороший мэтч | Показать в отчёте, записать в базу, готовить отклик |
| 50–69 | 🟡 Слабый мэтч | Показать в отчёте, записать в базу, готовить отклик / держать как fallback |
| <50 | ❌ Ниже порога | Не показывать в отчёте, учитывать в счётчике |

---

## 3. Критическое правило группы A

Группа A — обязательная.

Если хотя бы один критический параметр группы A не совпал, финальный балл **не может быть выше 49**.

Это значит:
- вакансия не показывается в отчёте;
- вакансия уходит в `<50`;
- cover letters не генерируются;
- в базу можно сохранить только как rejected / discarded, если нужна история.

---

## 4. Группа A — критические параметры, максимум 40

| # | Параметр | Вес |
|---:|---|---:|
| 1 | Специализация: Product Management | 10 |
| 2 | Формат работы: Remote / Hybrid Lisbon | 10 |
| 3 | Грейд: Senior / Middle | 10 |
| 4 | Тип занятости: Full-time | 5 |
| 5 | Локация: EU / Global Remote | 5 |

### Как трактовать

#### 1. Product Management — 10
Засчитывать, если роль явно:
- Product Manager;
- Senior Product Manager;
- Product Lead;
- Head of Product;
- Product Owner — только если есть ownership, roadmap, discovery, метрики, бизнес-результат.

Не засчитывать:
- Project Manager без Product;
- Marketing Manager;
- Operations Manager;
- Business Analyst без продуктовой ответственности;
- Program Manager без product ownership.

#### 2. Формат работы — 10
Засчитывать:
- Remote;
- Remote Europe;
- Remote EMEA;
- Global Remote;
- Hybrid Lisbon.

Не засчитывать:
- Office;
- Hybrid outside Lisbon;
- remote только внутри США / UK / другой несовместимой страны;
- relocation required.

#### 3. Грейд — 10
Засчитывать:
- Senior;
- Middle+;
- Product Lead;
- Group Product Manager;
- Head of Product, если команда небольшая.

Осторожно:
- Principal / Staff — можно засчитывать, если роль не требует глубокой enterprise-specialisation вне профиля.
- Junior / Associate — не засчитывать.

#### 4. Full-time — 5
Засчитывать:
- full-time;
- permanent;
- employment;
- long-term contract, если это полноценная роль.

Не засчитывать:
- part-time;
- internship;
- short-term freelance;
- advisory-only.

#### 5. EU / Global Remote — 5
Засчитывать:
- EU;
- EMEA;
- Portugal-compatible;
- Global Remote.

Не засчитывать:
- US-only;
- Canada-only;
- UK-only, если нет права работы;
- office/hybrid не в Лиссабоне.

---

## 5. Группа B — опыт и специализация, максимум 25

| # | Параметр | Вес |
|---:|---|---:|
| 6 | FinTech или eCommerce | 6 |
| 7 | B2B SaaS опыт | 5 |
| 8 | Управление продуктом: ownership, roadmap, discovery | 5 |
| 9 | Совпадение обязанностей с опытом кандидата | 5 |
| 10 | Совпадение задач: что реально делать | 4 |

### Как трактовать

#### 6. FinTech или eCommerce — 6
Полный балл, если домен:
- payments;
- banking;
- fintech infrastructure;
- billing;
- pricing;
- e-commerce;
- marketplaces;
- checkout;
- subscriptions.

Частичный балл можно дать за:
- SaaS monetisation;
- revenue platforms;
- commercial workflow products.

#### 7. B2B SaaS — 5
Полный балл, если продукт:
- B2B SaaS;
- internal platform for business users;
- enterprise SaaS;
- developer/productivity SaaS;
- workflow automation.

#### 8. Product ownership / roadmap / discovery — 5
Засчитывать, если в JD есть:
- roadmap ownership;
- product strategy;
- discovery;
- customer interviews;
- prioritisation;
- hypothesis testing;
- business outcome ownership.

#### 9. Совпадение обязанностей с опытом — 5
Сверять с профилем Руслана:
- growth;
- monetisation;
- pricing;
- B2B SaaS;
- FinTech;
- AI automation;
- analytics;
- onboarding;
- support automation;
- integrations.

#### 10. Совпадение реальных задач — 4
Засчитывать, если “что надо делать” похоже на прошлые задачи:
- запуск 0→1;
- рост ARPU;
- улучшение onboarding;
- product analytics;
- self-service;
- RAG / LLM workflows;
- platform/integration work;
- stakeholder management.

---

## 6. Группа C — навыки и инструменты, максимум 20

| # | Параметр | Вес |
|---:|---|---:|
| 11 | Аналитика: SQL, BI, data-driven | 4 |
| 12 | UI/UX опыт или работа с дизайном | 3 |
| 13 | Проектирование процессов | 3 |
| 14 | Английский B2+ | 3 |
| 15 | Agile / Scrum / Kanban | 2 |
| 16 | API / integrations / technical background | 2 |
| 17 | Работа с командой разработки | 3 |

### Как трактовать

#### 11. Analytics — 4
Засчитывать, если есть:
- SQL;
- BI;
- dashboards;
- metrics;
- experimentation;
- funnels;
- cohort analysis;
- data-informed decision-making.

#### 12. UI/UX — 3
Засчитывать, если есть:
- user flows;
- UX research;
- usability;
- Figma/wireframes;
- collaboration with design;
- conversion/onboarding optimisation.

#### 13. Process design — 3
Засчитывать:
- operational workflows;
- internal tools;
- support processes;
- onboarding process redesign;
- cross-functional process ownership.

#### 14. English B2+ — 3
Засчитывать по умолчанию, если роль англоязычная и нет требования native-level.

#### 15. Agile / Scrum / Kanban — 2
Засчитывать при упоминании:
- agile;
- scrum;
- kanban;
- sprint planning;
- delivery process;
- rituals.

#### 16. API / integrations / technical background — 2
Засчитывать, если роль требует:
- API;
- integrations;
- platform product;
- technical PM;
- data pipelines;
- AI/LLM tooling;
- developer-facing product.

#### 17. Development team collaboration — 3
Засчитывать, если есть:
- engineering collaboration;
- cross-functional teams;
- delivery with dev team;
- QA/design collaboration;
- stakeholder alignment.

---

## 7. Группа D — стратегия и рост, максимум 10

| # | Параметр | Вес |
|---:|---|---:|
| 18 | Growth / Monetization / Pricing | 3 |
| 19 | Запуск нового продукта / нового рынка | 2 |
| 20 | Работа с метриками: ARPU, LTV, NPS, DAU | 3 |
| 21 | Переговоры / stakeholders | 2 |

### Как трактовать

#### 18. Growth / monetisation / pricing — 3
Самый сильный сигнал для профиля Руслана:
- growth;
- PLG;
- pricing;
- packaging;
- upsell;
- cross-sell;
- revenue optimisation;
- activation;
- retention.

#### 19. New product / new market — 2
Засчитывать:
- 0→1 product;
- market expansion;
- new segment;
- new product line;
- MVP launch.

#### 20. Metrics — 3
Засчитывать:
- ARPU;
- LTV;
- retention;
- conversion;
- NPS;
- DAU/MAU;
- activation;
- funnel metrics;
- support/service metrics.

#### 21. Stakeholders — 2
Засчитывать:
- enterprise customers;
- sales;
- support;
- compliance;
- leadership;
- customer success;
- cross-functional negotiation.

---

## 8. Группа E — контекст компании, максимум 5

| # | Параметр | Вес |
|---:|---|---:|
| 22 | Компания из watchlist Tier 1 или Tier 2 | 2 |
| 23 | Продукт / рынок знаком кандидату | 1 |
| 24 | Стадия компании: scale-up или product-led growth | 1 |
| 25 | Компенсация соответствует уровню Senior | 1 |

### Как трактовать

#### 22. Watchlist Tier 1/2 — 2
Засчитывать, если компания входит в приоритетный список источников / компаний.

#### 23. Familiar product/market — 1
Засчитывать:
- SaaS;
- fintech;
- e-commerce;
- B2B workflows;
- AI automation;
- support/onboarding;
- pricing/monetisation.

#### 24. Scale-up / PLG — 1
Засчитывать, если компания:
- scale-up;
- growth-stage;
- product-led;
- has active expansion;
- has data/growth/product culture.

#### 25. Senior compensation — 1
Засчитывать, если:
- указана подходящая compensation band;
- роль senior/staff/lead уровня;
- компания market-rate;
- нет сигнала low-pay / junior budget.

---

## 9. Группа F — бонусы, максимум +5

Бонусы не отменяют критические правила группы A.  
Если A не пройдена, итог всё равно максимум 49.

| # | Параметр | Бонус |
|---:|---|---:|
| 26 | Упоминание конкретного продукта, с которым работал кандидат | +2 |
| 27 | Культура команды совпадает с ценностями кандидата | +1 |
| 28 | Срочный найм: ASAP / immediate start | +2 |

### Как трактовать

#### 26. Конкретный знакомый продукт — +2
Примеры:
- payments;
- checkout;
- pricing;
- billing;
- onboarding;
- support automation;
- AI assistant;
- analytics platform;
- CRM / internal tooling.

#### 27. Cultural fit — +1
Засчитывать, если есть:
- ownership;
- low bureaucracy;
- data-driven culture;
- product-led;
- hands-on PM;
- small autonomous teams.

#### 28. Urgent hiring — +2
Засчитывать:
- ASAP;
- immediate start;
- urgent hiring;
- fast process;
- role opened due to growth.

---

## 10. Формула расчёта

1. Проверить группу A.
2. Если любой параметр A = false:
   - `score = min(raw_score, 49)`;
   - `match_status = Ниже порога`;
   - не показывать в отчёте.
3. Если A пройдена:
   - `raw_score = A + B + C + D + E + F`;
   - `score = min(round(raw_score), 100)`.
4. Назначить статус:
   - 90–100: Excellent;
   - 70–89: Good;
   - 50–69: Weak;
   - <50: Rejected.

---

## 11. Рекомендуемый JSON для LLM extraction

```json
{
  "critical": {
    "product_management": {
      "value": true,
      "points": 10,
      "evidence": ["Senior Product Manager"]
    },
    "work_format_fit": {
      "value": true,
      "points": 10,
      "evidence": ["Remote Europe"]
    },
    "seniority_fit": {
      "value": true,
      "points": 10,
      "evidence": ["Senior"]
    },
    "full_time": {
      "value": true,
      "points": 5,
      "evidence": ["Full-time"]
    },
    "location_fit": {
      "value": true,
      "points": 5,
      "evidence": ["EMEA remote"]
    }
  },
  "experience": {
    "fintech_or_ecommerce": {
      "points": 6,
      "evidence": []
    },
    "b2b_saas": {
      "points": 5,
      "evidence": []
    },
    "ownership_roadmap_discovery": {
      "points": 5,
      "evidence": []
    },
    "responsibility_match": {
      "points": 5,
      "evidence": []
    },
    "task_match": {
      "points": 4,
      "evidence": []
    }
  },
  "skills": {},
  "strategy_growth": {},
  "company_context": {},
  "bonuses": {},
  "risks": [],
  "confidence": 0.0
}
```

---

## 12. Что нельзя делать

- Нельзя давать высокий балл, если локация несовместима.
- Нельзя засчитывать Project Manager как Product Manager без продуктового ownership.
- Нельзя выдавать score >100.
- Нельзя показывать вакансии <50.
- Нельзя генерировать cover letters для вакансий <50.
- Нельзя считать финальный балл руками LLM без проверяемого breakdown.
