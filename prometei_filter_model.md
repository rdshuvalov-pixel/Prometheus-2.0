# Vacancy Filter Model — Prometei

Версия: 2026-05-01  
Назначение: описать фильтры вакансий: какие применяются, когда применяются и зачем.

---

## 1. Главный принцип

Фильтры делятся на два этапа:

1. **Search-time filters** — минимальные фильтры на этапе поиска.
2. **Post-collection filters** — жёсткие фильтры после сбора вакансии.

Ключевое правило:  
**на этапе поиска не применять жёсткие фильтры по локации, remote/hybrid и full-time.**  
Сначала собрать сырые вакансии по роли, потом фильтровать и скорить.

---

## 2. Почему так

Если фильтровать слишком рано, система теряет хорошие вакансии из-за:
- кривой разметки job board;
- неполного описания;
- нестандартных формулировок типа `distributed team`, `remote-first`, `EMEA`;
- ATS, где локация указана только внутри JD;
- вакансий, где remote указан в тексте, но не в фильтре платформы.

Поэтому crawler собирает шире, а decision layer режет точнее.

---

## 3. Фильтры на этапе поиска

### 3.1 Что фильтровать

Искать по ключевым словам роли:

- Product Manager
- Senior Product Manager
- Product Lead
- Head of Product
- Product Owner — только если в выдаче явно продуктовая роль

### 3.2 Что НЕ фильтровать на этапе поиска

Не применять на этапе crawler/search:

- Remote;
- Hybrid;
- EU;
- Portugal;
- Lisbon;
- Full-time;
- salary;
- seniority;
- company stage.

Эти признаки извлекаются позже.

### 3.3 Зачем нужен широкий поиск

Цель search-stage — не принять решение, а собрать кандидатов в обработку.

Минимальные поля:

```json
{
  "company": "Company",
  "role_title": "Senior Product Manager",
  "platform": "Greenhouse",
  "tier": "Tier 1",
  "url": "https://..."
}
```

---

## 4. Исключения по роли

Сразу исключать, если очевидно:

| Роль | Правило |
|---|---|
| Project Manager | Исключить, если нет слова Product и нет product ownership |
| Marketing Manager | Исключить |
| Operations Manager | Исключить |
| Business Analyst | Исключить, если нет продуктовой составляющей |
| Program Manager | Исключить, если нет roadmap / product ownership |
| Product Marketing Manager | Обычно исключить, если это не PMM+Product hybrid |
| Growth Manager | Исключить, если нет product ownership |
| Product Designer | Исключить |
| Engineering Manager | Исключить |

---

## 5. Дедупликация

Дедуп — это фильтр качества данных, а не скоринг.

### 5.1 Базовый ключ

```text
company + normalized_role_title
```

### 5.2 Что считать дублем

Дубль, если:
- совпадает компания;
- совпадает нормализованное название роли;
- вакансия пришла с разных площадок, но ведёт к одной роли.

Пример:
- `Senior Product Manager - Growth`
- `Sr. Product Manager, Growth`
- `Senior PM Growth`

### 5.3 Что не считать дублем

Не дубль, если:
- та же компания, но другая продуктовая зона;
- та же роль, но новый reapply/posting спустя время;
- другая география или другая команда, если это явно отдельная вакансия.

### 5.4 Reapply rule

Если это повторный отклик спустя время:
- не перезаписывать старую запись;
- создать новую запись;
- добавить суффикс в `role_title`, например:
  - `[reapply YYYY-MM-DD]`;
  - `— повторный отклик DD.MM.YYYY`;
- в notes добавить ссылку / id предыдущей записи.

---

## 6. Первичные фильтры перед скорингом

Вакансия допускается к скорингу только если проходит все базовые условия.

| Фильтр | Значение |
|---|---|
| Роль | Product Manager / Product Lead / Head of Product |
| Формат | Remote или Hybrid Lisbon |
| Тип занятости | Full-time |
| Локация | EU или Global Remote |
| Свежесть | ≤5 дней, если дата известна |

---

## 7. Фильтр роли

### 7.1 Пропускать

- Product Manager;
- Senior Product Manager;
- Product Lead;
- Group Product Manager;
- Head of Product, если команда <5 человек или роль hands-on;
- Product Owner, если есть ownership, roadmap, discovery, metrics.

### 7.2 Отклонять

- чистый Project Manager;
- Delivery Manager;
- Scrum Master;
- Product Marketing Manager;
- Marketing Manager;
- Operations Manager;
- Business Analyst без product ownership;
- Customer Success Manager;
- Sales / BD;
- Engineering Manager.

### 7.3 Сомнительные случаи

Если роль называется неочевидно, смотреть на обязанности:

Пропускать, если есть:
- roadmap ownership;
- discovery;
- prioritisation;
- customer research;
- product metrics;
- GTM/product launch;
- responsibility for business outcome.

Отклонять, если обязанности:
- только координация;
- только delivery;
- только reporting;
- только marketing campaigns;
- только sales enablement без ownership продукта.

---

## 8. Фильтр формата работы

### 8.1 Пропускать

- Remote;
- Remote Europe;
- Remote EMEA;
- Global Remote;
- Remote Portugal;
- Hybrid Lisbon.

### 8.2 Отклонять

- Office;
- Hybrid не в Лиссабоне;
- relocation required;
- remote only US;
- remote only Canada;
- remote only UK, если нет права работы;
- remote only конкретная несовместимая страна.

### 8.3 Пометки совместимости

| Формат | Локация | Решение | Метка |
|---|---|---|---|
| Remote | EU | Пропустить | Remote EU ✅ |
| Remote | Global | Пропустить | Global Remote ✅ |
| Hybrid | Lisbon | Пропустить условно | Hybrid Lisbon ⚠️ |
| Hybrid | Other EU | Отклонить | Hybrid outside Lisbon ❌ |
| Office | Any | Отклонить | Office ❌ |

---

## 9. Фильтр локации

### 9.1 Пропускать

- Portugal;
- Lisbon;
- EU;
- EMEA;
- Europe;
- Global Remote;
- Worldwide;
- CET-compatible remote.

### 9.2 Отклонять

- US-only;
- Canada-only;
- LATAM-only;
- APAC-only, если требуется локальная зона/право работы;
- UK-only, если требуется UK work authorization;
- Germany-only hybrid/office;
- Spain-only hybrid/office;
- Netherlands-only hybrid/office;
- любые office/hybrid outside Lisbon.

### 9.3 Сомнительные случаи

Формулировки требуют LLM/classifier:

| Формулировка | Решение |
|---|---|
| `remote-first` | Проверить страновые ограничения |
| `distributed team` | Проверить payroll / legal entity |
| `must overlap EST` | Риск, но не reject автоматически |
| `Europe preferred` | Обычно pass |
| `based in Europe` | Pass |
| `must be located in US` | Reject |
| `authorized to work in US` | Reject |

---

## 10. Фильтр типа занятости

### 10.1 Пропускать

- Full-time;
- Permanent;
- Employment;
- Long-term contract, если это полноценная продуктовая роль.

### 10.2 Отклонять

- Part-time;
- Internship;
- Temporary;
- Short-term freelance;
- Advisory-only;
- Fractional PM, если занятость явно неполная.

### 10.3 Если тип занятости не указан

Не отклонять автоматически.  
Добавить предупреждение:

```text
⚠️ Тип занятости не указан
```

Дальше скорить по доступным данным.

---

## 11. Фильтр свежести

### 11.1 Жёсткое правило

Брать вакансии, опубликованные **не старше 5 дней**.

### 11.2 Если дата известна

| Дата | Решение |
|---|---|
| 0–5 дней | Пропустить |
| >5 дней | Отклонить |
| закрытая / expired | Отклонить |

### 11.3 Если дата неизвестна

Не отклонять.  
Скорить и сохранять, но добавить предупреждение:

```text
⚠️ Дата публикации неизвестна
```

### 11.4 Зачем такой фильтр

Цель — попадать в свежую волну кандидатов, пока:
- роль не перегрета;
- hiring manager ещё смотрит новые отклики;
- слот интервью не забит.

---

## 12. Фильтр языка

### 12.1 Пропускать

- English;
- Russian;
- English/Russian.

### 12.2 Отклонять или снижать score

- обязательный German C1;
- обязательный French C1;
- обязательный Spanish C1;
- любой локальный язык, если это hard requirement.

Если локальный язык “nice to have” — не отклонять, но учесть как риск.

---

## 13. Фильтр зарплаты / компенсации

### 13.1 Если компенсация указана

Пропускать, если соответствует Senior PM уровню.

Отклонять или снижать score, если:
- явно junior budget;
- сильно ниже рынка;
- unpaid / equity-only;
- commission-only.

### 13.2 Если компенсация не указана

Не отклонять.  
Компенсация влияет на score только при наличии данных.

---

## 14. Фильтр домена

Домен **не является жёстким фильтром**, если роль проходит критические параметры.

### 14.1 Приоритетные домены

- B2B SaaS;
- FinTech;
- Payments;
- Banking;
- eCommerce;
- Pricing;
- Monetisation;
- AI products;
- Platform products;
- Developer tools;
- Analytics / BI;
- CRM / workflow automation.

### 14.2 Слабые домены

Не отклонять автоматически, но снижать score:

- gaming;
- gambling;
- pure consumer social;
- healthcare без B2B/product complexity;
- content/media без monetisation/product analytics;
- HR/recruiting без SaaS depth.

### 14.3 Запрещённые / нежелательные домены

Можно отклонять или переводить в weak:
- откровенный adult;
- high-risk gambling;
- scammy crypto;
- серые финансы;
- pure casino.

---

## 15. Фильтр компании

### 15.1 Watchlist

Компании из Tier 1–2 получают плюс в скоринге, но это не жёсткий фильтр.

### 15.2 Не отклонять только потому что компания неизвестна

Если JD сильный:
- remote;
- product role;
- B2B SaaS / fintech / AI;
- senior;
- full-time;

то вакансию можно брать даже вне watchlist.

---

## 16. Фильтр по описанию вакансии

### 16.1 Если описание короткое

Если JD <100 слов:
- не придумывать требования;
- скорить по доступным параметрам;
- добавить риск:

```text
Недостаточно данных — описание короткое
```

### 16.2 Если описание пустое

Сохранять только минимально, если:
- компания сильная;
- роль явно подходит;
- есть нормальный URL.

Иначе reject как insufficient data.

---

## 17. Правило показа в отчёте

Показывать только:

```text
score >= 50
AND location compatible
AND not duplicate
AND role compatible
```

Не показывать:
- <50;
- дубли;
- office;
- hybrid outside Lisbon;
- expired;
- не Product.

---

## 18. Что происходит после фильтра

### Если вакансия прошла

1. Запустить scoring.
2. Сгенерировать:
   - why fit;
   - risks;
   - conclusion.
3. Если score ≥50:
   - записать в Supabase;
   - сгенерировать formal cover letter;
   - сгенерировать informal message;
   - показать в отчёте.

### Если вакансия не прошла

1. Не показывать в основном отчёте.
2. Увеличить соответствующий счётчик:
   - below threshold;
   - duplicate;
   - rejected by date;
   - rejected by location;
   - rejected by role.
3. При необходимости сохранить reason.

---

## 19. Рекомендуемый JSON для filter decision

```json
{
  "job_id": "string",
  "company": "string",
  "role_title": "string",
  "filters": {
    "role": {
      "passed": true,
      "value": "Senior Product Manager",
      "reason": "Product ownership role",
      "evidence": ["Senior Product Manager"]
    },
    "work_format": {
      "passed": true,
      "value": "Remote",
      "reason": "Remote Europe supported",
      "evidence": ["Remote - Europe"]
    },
    "employment_type": {
      "passed": true,
      "value": "Full-time",
      "reason": "Full-time role",
      "evidence": ["Full-time"]
    },
    "location": {
      "passed": true,
      "value": "Europe",
      "reason": "EU-compatible",
      "evidence": ["EMEA"]
    },
    "freshness": {
      "passed": true,
      "value": "unknown",
      "reason": "Date not stated; allowed with warning",
      "warning": "⚠️ Дата публикации неизвестна",
      "evidence": []
    }
  },
  "overall_decision": "pass_to_scoring",
  "reject_reason": null,
  "warnings": []
}
```

---

## 20. Канонические reject reasons

Использовать фиксированные причины, чтобы потом строить аналитику:

```text
not_product_role
project_manager_only
marketing_role
operations_role
business_analyst_no_product
office_only
hybrid_outside_lisbon
us_only
uk_only_without_work_rights
expired_or_old
part_time
internship
duplicate
insufficient_data
low_salary
domain_mismatch
```

---

## 21. Канонические warnings

```text
date_unknown
employment_type_unknown
salary_unknown
location_ambiguous
remote_policy_ambiguous
short_description
domain_risk
seniority_too_high
seniority_too_low
requires_travel
requires_local_language
```

---

## 22. Что нельзя делать

- Нельзя фильтровать по remote/location на этапе crawler слишком рано.
- Нельзя пропускать дедуп.
- Нельзя показывать office/hybrid outside Lisbon.
- Нельзя отклонять вакансию только потому, что дата неизвестна.
- Нельзя придумывать требования, если описание короткое.
- Нельзя сохранять как strong match вакансию, у которой провалена группа A.
