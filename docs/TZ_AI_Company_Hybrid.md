# ТЗ: AI-компания ROMAN — гибридная версия

> Собрано из двух черновиков: продуктовое ТЗ (бренды/контент/оргструктура) + инженерное ТЗ (архитектура/безопасность/фазы). Топ-агент унифицирован под именем **Татьяна**.

---

## 0. Главный принцип

Роман — единственный финальный руководитель.

Иерархия: **Роман → Татьяна (AI COO) → руководители направлений → специалисты → субагенты.**

Система не просто отвечает в чате — она сама организует, выполняет, проверяет и улучшает работу.

Роман ставит цель → система определяет, кто выполняет → делегирует → проверяет → исправляет → возвращает готовый результат.

**Продуктовый North Star:** Роман формулирует цель, а не управляет операционкой. Система превращает `GOAL → STRATEGY → RESEARCH → CONTENT → PRODUCTION → DISTRIBUTION → ANALYTICS → KNOWLEDGE → IMPROVEMENT`. Стратегический контроль всегда остаётся у Романа.

**UX-принцип:** Роман не управляет 20+ агентами вручную. Основной канал — Telegram, основной собеседник — Татьяна. Она сама решает WHO / WHAT / WHEN / WITH WHICH MODEL / WITH WHICH TOOL / AT WHAT COST. Роман вмешивается только там, где нужно решение.

---

## 1. Татьяна — AI COO

Главный AI-руководитель, правая рука Романа, главнее всех агентов кроме него.

Функции: планирование, постановка задач, распределение работы, управление агентами, создание команд, контроль сроков и качества, финальный QA, контроль AI-бюджета, ведение памяти, отчётность, оптимизация процессов, эскалация важных решений.

**Owner override-команды (через Telegram):**
- `/stop` — немедленно останавливает все новые автоматические actions
- `/pause publishing` — останавливает публикации
- `/kill task <ID>` — останавливает конкретный workflow

---

## 2. Архитектура памяти

Единая система памяти проекта хранит: цели и решения Романа, Brand DNA, структуру компании, агентов и роли, текущие проекты, research, лучшие форматы/hooks, результаты публикаций, ошибки, lessons learned, экономику проектов.

Память общая для команды, но с разграничением доступа (RBAC). Организовать как единый knowledge base (Obsidian или файловая система + `knowledge_documents` / `embeddings` в БД).

---

## 3. Департаменты

- **AI Media / Content** — производство контента, медиабренды
- **Research / Intelligence** — тренды, рынок, новости, конкуренты, фактчек
- **Marketing / Growth** — SEO, GEO, SMM, продвижение, аналитика
- **CRM / Sales** — лиды, CRM, автоматизация продаж, follow-up
- **Software / App Development** — приложения, платформы, боты, SaaS
- **Finance / Crypto** — финансовая аналитика, крипто, торговые системы
- **Automation / Infrastructure** — API, MCP, интеграции, инфраструктура

---

## 4. Media Department — 9 брендов

Единый центральный контент-конвейер адаптирует контент под все бренды. Отдельной огромной команды под каждый бренд не создавать.

| # | Бренд | Темы | Монетизация (в перспективе) |
|---|-------|------|------------------------------|
| 1 | **ROMAN** (флагман) | финансы, крипто, AI, технологии, автономность, мышление, бизнес, личный опыт | личный бренд, реальное лицо/голос + Digital Avatar |
| 2 | **AUTONOMY** | автономные дома, теплицы, вода, энергия, энергонезависимость | Telegram-сообщество → платное → консультации/продукты |
| 3 | **HEALTH** | питание, привычки, активность, longevity (мед. утверждения — только с фактчеком) | продукты, обучение, партнёрки |
| 4 | **RELIGION/SPIRITUALITY** | Бог, Тора, Библия, Коран, духовность, философия | сообщество, книги, донаты |
| 5 | **MOTIVATION** | дисциплина, мышление, истории предпринимателей (цитаты — проверять подлинность) | — |
| 6 | **ALTERNATIVE WORLD** (раб. название) | альтернативный взгляд на привычные вещи, образование, культура | — |
| 7 | **NEWS** | «что новость означает на самом деле» — источник → факты → интерпретации → последствия | — |
| 8 | **VISA/PASSPORT/TRAVEL** (коммерческий) | визы, вторые паспорта, ВНЖ, travel hacks | сразу: контент → трафик → заявка → CRM → продажа |
| 9 | **PRO AI** / **PRO AI VC** | AI-модели, инструменты, агенты, эксперименты, стартапы | обучение, консультации, VC-направление |

### Content pipeline — 3 режима
- **MODE 1 — TREND**: Роман даёт ссылку на вирусный ролик → research → анализ вирусности (hook, структура, эмоц. триггеры, темп) → выделение Transferable Pattern → оригинальный сценарий (не копия) → фактчек → production → QA
- **MODE 2 — ROMAN RAW**: Роман грузит сырое видео → транскрипция → лучшие моменты → удаление мусора → hook → B-roll/субтитры/музыка/CTA → версии под платформы, с сохранением манеры речи
- **MODE 3 — ROMAN IDEA**: Роман голосом даёт идею → Татьяна сама запускает весь pipeline

Один исходник → YouTube, Shorts, Reels, TikTok, Facebook Reels, X, Telegram, карусели, текстовые посты.

### AI Digital Avatar
Приоритет: реальный Роман → гибрид → Digital Avatar → полностью AI. Оценить HeyGen, SYNTX.AI, ElevenLabs и др. по критерию: качество + стоимость + API/MCP + автоматизация — не привязываться заранее к сервису.

---

## 5. Экономика и оптимизация AI

Учёт стоимости по каждой единице контента: research, сценарий, fact-check, QA, generation, avatar, voice, монтаж, API, повторные итерации → итоговая стоимость. После первых 10 роликов — среднее/медиана/мин/макс, прогноз на 10/50/100/500.

**Принцип роутинга моделей:** дешёвая модель → простые задачи (классификация, массовый research, rewriting); сильная модель → только стратегия, сложный анализ, финальный QA, архитектура. Перед крупными задачами — оценка предполагаемого расхода.

Аудит системы каждые 5 дней: память, дедупликация задач, расходы, prompts, workflows, узкие места.

---

## 6. Инженерная архитектура

### 6.1 Схема данных (ключевые таблицы)
```
users, brands, agents, agent_runs, tasks, workflows,
content_items, content_versions, campaigns,
platform_accounts, publications, assets, sources,
research_items, approvals, metrics, experiments, insights,
prompts, prompt_versions,
courses, modules, lessons, quiz_items,
knowledge_documents, embeddings,
integrations, webhooks, audit_logs, llm_usage
```
Создать migrations для всех таблиц.

### 6.2 Security (обязательно)
Secret manager / env variables, encryption where appropriate, RBAC, input validation, rate limiting, webhook verification, Telegram user allowlist, audit logging, least privilege, API token rotation, prompt-injection protection, tool permission boundaries. Никогда не коммитить secrets — `.env.example` без реальных ключей.

### 6.3 Prompt-injection defense
Внешний контент (веб-страницы, комментарии, документы, посты конкурентов) — **untrusted data**. Research-агенты не выполняют инструкции из него. Чёткое разделение: SYSTEM INSTRUCTIONS / TRUSTED OWNER INSTRUCTIONS / EXTERNAL DATA.

### 6.4 Failure handling
Retry, timeout, idempotency, dead-letter queue, partial failure, provider fallback, manual retry. Publishing — обязательно idempotent (нельзя случайно опубликовать пост дважды).

### 6.5 Testing
Unit, integration, API, agent schema tests, workflow tests, permission tests, publishing mocks, LLM provider mocks. Critical workflows — E2E tests.

### 6.6 Репозиторий (monorepo)
```
/apps        — api, web, telegram
/packages    — agents, ai, database, workflows, integrations,
               analytics, knowledge, prompts, shared, ui
/infrastructure
/docs
/tests
```

### 6.7 Claude Code / CLAUDE.md
Описать: architecture, coding conventions, commands, testing rules, security rules, agent rules, database rules, API conventions, definition of done. Использовать возможности Claude Code/MCP только после проверки актуальной документации. Минимально необходимые permissions, без dangerous permission bypass в production.

### 6.8 Документация
`README.md, ARCHITECTURE.md, SECURITY.md, AGENTS.md, WORKFLOWS.md, INTEGRATIONS.md, DEPLOYMENT.md, DATABASE.md, API.md, TELEGRAM.md, CONTENT_PIPELINE.md, EDUCATION_ENGINE.md, ANALYTICS.md, COST_CONTROL.md`

### 6.9 Инженерные принципы
SOLID; DRY без preemptive-абстракций; typed contracts; schema validation; idempotency; observability; testability; provider independence; security by default; human approval для необратимых действий; cost awareness; versioned prompts/content; source traceability. **Не** гигантский god-class оркестратор, **не** десятки микросервисов без нужды — начать с modular monolith + workers, с возможностью выделить сервисы позже.

### 6.10 MCP / Skills / Integrations
Подключать только реально нужные для текущего workflow: web research, Google Drive, email, calendar, CRM, GitHub, social media, video production, AI avatar, analytics, публикация.

---

## 7. Контроль качества

Перед выдачей результата: агент → руководитель направления → Татьяна → Роман. Плохой результат не отдаётся Роману — возвращается на доработку.

**Финальная отчётность по задаче:**
```
STATUS
Что сделано: ...
Что не сделано: ...
Что требует решения Романа: ...
Стоимость: $...
Использованные модели: ...
Следующий шаг: ...
Spent: $X / Remaining: $X
```

---

## 8. Фазы реализации

| Фаза | Содержание |
|------|-----------|
| **0 — Research & Architecture** | Technology Audit (Claude Code, Anthropic/OpenAI/Google AI API, Telegram Bot API, Metricool, Make/n8n, Canva, соц. платформы, video/image providers — статус: AVAILABLE / LIMITED / PAID / NOT AVAILABLE / UNKNOWN, без предположений); ARCHITECTURE.md (диаграмма системы, иерархия агентов, data/event flow, security boundaries, LLM routing); ADR по framework/DB/queue/LLM abstraction/MCP/publishing/storage/deployment; IMPLEMENTATION_PLAN.md с приоритетами P0–P3 |
| **1 — Core** | Telegram Owner Interface, Татьяна (Chief of Staff), Agent Registry, Task Engine, PostgreSQL, Redis, LLM Router, Memory, Research, Strategy, Content Planner, Scriptwriter, Approval Engine, Content Pipeline, базовый dashboard |
| **2 — Distribution** | Соц. публикация (напр. Metricool), календарь, platform-агенты, analytics ingestion |
| **3 — Media Factory** | Image/video generation, Canva, asset pipeline, субтитры, media QA |
| **4 — Education** | Curriculum, courses, lessons, quizzes, education publishing |
| **5 — Intelligence** | Trend Radar, competitor intelligence, эксперименты, content scoring, рекомендательный движок |
| **6 — Autonomy** | Continuous optimization, продвинутый routing, multi-brand support, продвинутая аналитика |

**MVP считается готовым только при полном рабочем цикле:**
```
OWNER TELEGRAM MESSAGE → ТАТЬЯНА → TASK DECOMPOSITION → RESEARCH → STRATEGY
→ CONTENT PLAN → SCRIPT → OWNER APPROVAL → SCHEDULING → PUBLICATION
→ METRICS → ANALYSIS → MEMORY UPDATE → NEXT RECOMMENDATION
```
Красивый dashboard без рабочего цикла — не MVP.

---

## 9. Порядок работы для Claude / Claude Code

Не писать сразу весь проект. Пошагово:

1. **Research** — Technology Audit → `docs/TECHNOLOGY_AUDIT.md`
2. **Architecture** — `docs/ARCHITECTURE.md`
3. **ADR** — architecture decision records по ключевым техвыборам
4. **Implementation Plan** — `docs/IMPLEMENTATION_PLAN.md` (P0–P3, для каждой задачи: objective, dependencies, files, tests, acceptance criteria)
5. **Scaffold** — структура репозитория
6. **Core implementation** — Фаза 1 полностью. Без fake-реализаций «для вида»; если нужны credentials — adapter + mock + setup-документация
7. **Verify** — lint, typecheck, tests, build до green state
8. **Security review** — самостоятельный threat-model и code review
9. **Report** — IMPLEMENTED / TESTED / MOCKED / REQUIRES CREDENTIALS / BLOCKED / NEXT PRIORITY

**Когда спрашивать Романа** — только если решение: существенно меняет бизнес-модель; требует платного сервиса; требует credentials; создаёт необратимые последствия; влияет на безопасность; требует стратегического выбора владельца. Во всех остальных случаях: исследовать → обоснованно решить → задокументировать → реализовать → протестировать.

---

## 10. Итоговое требование

Сначала: проанализировать это ТЗ → предложить оптимальную архитектуру → определить агентов, иерархию, workflows, память, skills/MCP, файловую структуру → создать тестовый проект → провести первый end-to-end тест → показать результат Роману → после одобрения масштабировать.

Роман — единственный финальный руководитель. Татьяна — AI COO и правая рука. Остальные агенты работают через неё или через руководителей направлений.
