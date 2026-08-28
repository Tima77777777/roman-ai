# Telegram → GitHub bridge (Cloudflare Worker)

Код написан и протестирован (`npx tsc --noEmit` — чисто). Деплой требует действий владельца (создание аккаунта, секреты) — ниже точные шаги.

## Что делает

Принимает вебхук от Telegram-бота, проверяет отправителя (только `OWNER_TELEGRAM_ID`) и секрет вебхука, создаёт GitHub Issue с текстом задачи. Дальше `.github/workflows/telegram-issue-trigger.yml` (P1, ещё не написан) будит облачную Claude Code Routine по событию Issue.

## Деплой (только владелец — новый аккаунт/секреты)

1. Зарегистрироваться на [cloudflare.com](https://cloudflare.com) (бесплатно, карта не нужна — см. Technology Audit, раздел "Мост Telegram→GitHub").
2. `npm install` в этой папке.
3. `npx wrangler login` — авторизация в браузере.
4. Секреты (каждый — `npx wrangler secret put <ИМЯ>`, вставить значение по запросу):
   - `TELEGRAM_BOT_TOKEN` — тот же токен, что уже в `.env`.
   - `TELEGRAM_WEBHOOK_SECRET` — придумать любую случайную строку (например `openssl rand -hex 32`).
   - `GITHUB_TOKEN` — токен с scope `repo` (тот же, что используется для push, либо отдельный).
   - `OWNER_TELEGRAM_ID` — `8796085265`.
5. `npm run deploy` — вернёт URL вида `https://roman-ai-telegram-bridge.<subdomain>.workers.dev`.
6. Зарегистрировать вебхук у Telegram (замените `<TOKEN>`, `<WORKER_URL>`, `<SECRET>` на реальные значения):
   ```
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WORKER_URL>&secret_token=<SECRET>"
   ```

После этого локальный `CronCreate`-поллер (7 минут) можно отключить — реакция станет практически мгновенной.
