<div align="center">

# Healthy Elf Wealthy Elf 🧝‍♀️💰

**Telegram bot that turns free-text messages into health and finance logs, with XP and streaks.**

![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/-Telegram-26A5E4?logo=telegram&logoColor=white)
![Claude AI](https://img.shields.io/badge/-Claude%20AI-D97706)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-AGPLv3%20%2B%20Commercial-00D4C8.svg)

</div>

---

## What it does

Healthy Elf Wealthy Elf is a Telegram bot that tracks personal health habits (sleep, water, workout, mood) and finances (expenses) through plain free-text logging — no forms, no menus. Just tell it "slept 7.5 hrs" or "$12 lunch at toast box" and Claude parses the message into a structured entry. Health logs build daily streaks and Healthy Elf XP; expense logs build Wealthy Elf XP. `/status` shows your current XP, streaks, and the last 7 days' spend by category.

## Features

- Free-text logging for both health and finance — Claude parses your message into a structured entry (habit type/amount + category)
- Daily streak tracking per health habit (sleep, water, workout, mood)
- Combined XP counters: Healthy Elf XP and Wealthy Elf XP (+10 per logged entry in the MVP)
- `/status` — current XP, streaks, and last 7 days' spend by category
- `/start` and `/help` commands with example prompts
- SQLite storage, works out of the box with no external database
- Two run modes: local polling for dev, FastAPI webhook for deployment

## Tech Stack

| Layer | Choice |
|---|---|
| Bot | python-telegram-bot |
| AI parsing | Anthropic Claude API |
| Web server (webhook mode) | FastAPI + uvicorn |
| Storage | SQLite |
| Hosting | Docker / Zeabur |

## Screenshots

_Screenshots coming soon._

## Quick Start

### Local dev (polling mode)

```bash
cd healthy-elf-wealthy-elf
pip install -r requirements.txt
cp .env.example .env   # fill in TELEGRAM_BOT_TOKEN and ANTHROPIC_API_KEY
cd app
export $(cat ../.env | xargs)   # or use python-dotenv if you prefer
python bot.py
```

This runs the bot in polling mode — good for local testing, no public URL needed.

### Deploy to Zeabur (webhook mode)

1. Push this repo to GitHub.
2. Create a new Zeabur service from the repo (Dockerfile is included).
3. Set environment variables in Zeabur: `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`.
4. Once deployed, set your Telegram webhook to Zeabur's public URL:

```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://<your-zeabur-domain>/telegram/webhook"
```

5. `main.py` runs the FastAPI app; the bot processes updates via the `/telegram/webhook` POST endpoint instead of polling.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from @BotFather |
| `ANTHROPIC_API_KEY` | Yes | Claude API key from Anthropic |
| `DB_PATH` | No | SQLite file path (default `healthy_elf_wealthy_elf.db`) |

## Project Structure

```
healthy-elf-wealthy-elf/
├── Dockerfile
├── requirements.txt
├── .env.example
├── README.md
└── app/
    ├── config.py         # env vars, XP constants
    ├── db.py              # SQLite schema + CRUD (users, logs, streaks)
    ├── claude_parser.py   # Claude API call: free text -> structured log
    ├── bot.py             # Telegram handlers (/start /status /help, free text)
    └── main.py            # FastAPI wrapper for webhook deployment
```

## Status / Roadmap

- [x] Free-text health + finance logging via Claude
- [x] Daily streaks per health habit
- [x] Healthy Elf XP / Wealthy Elf XP counters
- [x] `/status` summary command
- [x] Polling (dev) and FastAPI webhook (production) modes
- [ ] Budgets & warnings — per-category monthly limits, soft alerts when close to over
- [ ] Weekly digest — auto-posted Sunday summary (health streaks + spend breakdown)
- [ ] Achievements/badges — 30-day streaks, under-budget-4-weeks, etc.
- [ ] Savings rate tracking — Wealthy Elf XP tied to hitting savings goals, not just logging
- [ ] Photo-based logging — snap a receipt or meal photo, Claude extracts the data
- [ ] Mini webapp dashboard

## Changelog

- **Jul 2026** — Initial release: free-text health/finance logging via Claude, streaks, XP counters, `/status`, and both polling and FastAPI webhook run modes

## License

This project is dual licensed.

- Community Edition — [GNU Affero General Public License v3 (AGPLv3)](LICENSE). Free to use, modify, and self-host. If you distribute a modified version or run it as a network service, you must make the corresponding source available.
- Commercial License — for organisations that want to embed, modify, or distribute this software without AGPLv3's obligations. See [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).

---

<div align="center">
<sub>Built by <a href="https://github.com/TheBooleanJulian">@TheBooleanJulian</a></sub>
</div>
