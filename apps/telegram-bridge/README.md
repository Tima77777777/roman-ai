# Telegram → GitHub bridge (Cloudflare Worker)

Код написан, задеплоен и проверен вживую синтетическими запросами (2026-09-01): `https://roman-ai-telegram-bridge.tima-apps.workers.dev`. Секрет-проверка, owner-only allowlist и создание GitHub Issue подтверждены на реальном воркере (403 на неверный секрет, тихий 200 для чужих отправителей, реальный Issue создан для владельца — тестовый issue закрыт после проверки).

## Что делает

Принимает вебхук от Telegram-бота, проверяет отправителя (только `OWNER_TELEGRAM_ID`) и секрет вебхука, создаёт GitHub Issue с текстом задачи. Дальше `.github/workflows/telegram-issue-trigger.yml` (P1, ещё не написан) будит облачную Claude Code Routine по событию Issue.

## Статус переключения (важно)

Воркер задеплоен, но реальный вебхук Telegram-бота на него **намеренно не переключён**. Причина: `.github/workflows/telegram-issue-trigger.yml` ещё не написан (зависит от подключения GitHub App к claude.ai Routines, см. `docs/ARCHITECTURE.md` раздел 3.2 — всё ещё `401`) — без него создаваемые мостом issues никто не обрабатывает, и переключение вебхука сейчас означало бы тихую потерю реакции на сообщения Романа вместо улучшения. Локальный `CronCreate`-поллер остаётся основным каналом до тех пор, пока цепочка Issue → Routine не подтверждена целиком.

Когда цепочка будет готова, переключение — это одна команда (значения секрета и URL уже в Cloudflare, не нужно их запоминать/хранить отдельно):
```
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://roman-ai-telegram-bridge.tima-apps.workers.dev&secret_token=<TELEGRAM_WEBHOOK_SECRET-из-Cloudflare>"
```
После переключения локальный поллер можно отключить — реакция станет практически мгновенной вместо задержки до 7 минут.

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
6. Регистрация вебхука у Telegram — см. "Статус переключения" выше, отложено до готовности Issue → Routine цепочки.
