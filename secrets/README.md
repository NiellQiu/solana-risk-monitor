# Secrets folder (local only)

Put API keys **only** in `local.env` here. This file is **gitignored** and will not be pushed to GitHub.

## Setup

1. Copy `local.env.example` to `local.env`.
2. Open `local.env` and paste your real URLs/keys (one per line).
3. Restart the app so settings reload.

You can also use the project root `.env` file — both are loaded (root `.env` first, then `secrets/local.env`).

## What else to add (optional, free tier)

| Priority | Name | Purpose |
|----------|------|--------|
| Done | **Helius RPC** | Real Solana chain reads (`HELIUS_RPC_URL`) |
| Default | **DexScreener** | Free public API for token discovery + pair stats (no key; ~60 req/min) |
| Optional | **Birdeye** | Alternate discovery if you set `BIRDEYE_API_KEY` |
| Medium | **RugCheck** | Extra safety signals (already used via public base URL; key if they offer one) |
| Alerts | **Telegram Bot API** | Phone alerts (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) — not required for monitoring |

Without **Birdeye** (or similar), token discovery may fall back to sample data until we add a Helius-only discovery path.

## Security

Never commit `local.env`. Never paste keys in Discord/chat/screenshots. Rotate keys if exposed.
