/**
 * Cloudflare Worker bridge: Telegram webhook -> GitHub Issue -> wakes a Claude Code
 * Cloud Routine via GitHub Actions (docs/ARCHITECTURE.md, раздел 3.2; ADR-003).
 *
 * Replaces the ~7-minute local CronCreate poller with a near-instant path once deployed.
 *
 * Secrets (set via `wrangler secret put <NAME>`, never committed):
 *   TELEGRAM_BOT_TOKEN     — used only to verify this is really our bot's webhook
 *   TELEGRAM_WEBHOOK_SECRET — the secret_token registered with setWebhook (see README)
 *   GITHUB_TOKEN           — a token with `repo` scope, used to create the Issue
 *   OWNER_TELEGRAM_ID       — numeric Telegram id allowed to issue commands (policy.json: owner-only)
 */

export interface Env {
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_WEBHOOK_SECRET: string;
  GITHUB_TOKEN: string;
  OWNER_TELEGRAM_ID: string;
  GITHUB_REPO: string; // "Tima77777777/roman-ai"
}

interface TelegramMessage {
  message_id: number;
  from?: { id: number };
  text?: string;
  voice?: { file_id: string };
}

interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
}

async function createGitHubIssue(env: Env, title: string, body: string): Promise<Response> {
  return fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/issues`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "roman-ai-telegram-bridge",
    },
    body: JSON.stringify({ title, body, labels: ["telegram-command"] }),
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Telegram sends this header when secret_token was set via setWebhook — rejects spoofed calls.
    const secretHeader = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (secretHeader !== env.TELEGRAM_WEBHOOK_SECRET) {
      return new Response("Forbidden", { status: 403 });
    }

    const update = (await request.json()) as TelegramUpdate;
    const message = update.message;

    // Owner-only allowlist — same rule as the local poller (docs/ARCHITECTURE.md, раздел 1.3).
    if (!message || !message.from || String(message.from.id) !== env.OWNER_TELEGRAM_ID) {
      return new Response("OK", { status: 200 }); // ack silently, don't leak info to non-owner senders
    }

    const taskText = message.text
      ? message.text
      : message.voice
        ? `[voice message, file_id=${message.voice.file_id} — needs transcription, see scripts/transcribe.py]`
        : "[unsupported message type]";

    const issueResponse = await createGitHubIssue(
      env,
      `Telegram command #${message.message_id}`,
      taskText,
    );

    if (!issueResponse.ok) {
      // Fail loudly in the Worker's own logs, but still ack Telegram so it doesn't retry-storm us.
      console.error(`GitHub issue creation failed: ${issueResponse.status} ${await issueResponse.text()}`);
    }

    return new Response("OK", { status: 200 });
  },
};
