# Telegram → GitHub bridge (Cloudflare Worker)

Код написан, задеплоен, проверен вживую (2026-09-01, синтетическими запросами; 2026-09-04 — реальным сообщением владельца): `https://roman-ai-telegram-bridge.tima-apps.workers.dev`. Секрет-проверка, owner-only allowlist и создание GitHub Issue подтверждены на реальном воркере.

## Что делает

Принимает вебхук от Telegram-бота, проверяет отправителя (только `OWNER_TELEGRAM_ID`) и секрет вебхука, создаёт GitHub Issue с текстом задачи (label `telegram-command`). Дальше открытие Issue (`issues.opened`) напрямую будит облачную Claude Code Routine "Telegram poller" через вебхук-триггер (`RemoteTrigger.create_webhook_trigger`, подключён к репозиторию API-вызовом) — **без** промежуточного GitHub Actions workflow, как планировалось изначально; такой workflow не написан и не нужен.

## Статус переключения

**С 2026-09-04 — основной и единственный активный канал.** Реальный вебхук Telegram-бота переключён на этот Worker (`setWebhook`, секрет сгенерирован заново при переключении). Цепочка Telegram → Worker → GitHub Issue → webhook-триггер → Routine → ответ в Telegram проверена вживую целиком, задержка от сообщения до пробуждения Routine — единицы секунд. Часовой `getUpdates`-поллер (локальный `CronCreate` и часовой cron самой Routine) отключён, оставлен как резерв — см. `docs/ARCHITECTURE.md` раздел 3.1.

Для справки, команда переключения (уже выполнена, приведена как документация на случай пересоздания секрета):
```
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://roman-ai-telegram-bridge.tima-apps.workers.dev&secret_token=<TELEGRAM_WEBHOOK_SECRET-из-Cloudflare>"
```
Откат на polling (если понадобится): `deleteWebhook`, затем вернуть `cron_expression` Routine в `"33 * * * *"` через `RemoteTrigger.update`.

## Деплой (уже выполнено, шаги ниже — для справки/пересоздания)

1. Аккаунт Cloudflare — тот же, что используется для fin-tracker-bot на этой машине (был создан для другого проекта, подошёл и сюда — отдельной регистрации не понадобилось).
2. `npm install` в этой папке.
3. `npx wrangler login` — авторизация в браузере (уже выполнена, токен закэширован локально).
4. Секреты (каждый — `npx wrangler secret put <ИМЯ>`, вставить значение по запросу):
   - `TELEGRAM_BOT_TOKEN` — тот же токен, что уже в `.env`.
   - `TELEGRAM_WEBHOOK_SECRET` — случайная строка (`openssl rand -hex 32`), сгенерирована и установлена, нигде не сохранена в файлах репозитория.
   - `GITHUB_TOKEN` — токен с scope `repo` (тот же, что используется для push).
   - `OWNER_TELEGRAM_ID` — `8796085265`.
5. `npm run deploy` — вернул `https://roman-ai-telegram-bridge.tima-apps.workers.dev`.
6. Регистрация вебхука у Telegram — выполнено 2026-09-04, см. "Статус переключения" выше.
