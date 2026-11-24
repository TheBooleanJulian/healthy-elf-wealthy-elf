"""
Telegram bot handlers for Healthy Elf Wealthy Elf (MVP).

Commands:
  /start   - register user, show intro
  /status  - show XP, streaks, and last 7 days' spend by category
  /help    - list what you can log

Everything else is free text, routed through claude_parser to detect
whether it's a health log or a finance log.
"""

import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
import db
from claude_parser import parse_log_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WELCOME = (
    "🧝‍♀️💰 Welcome to Healthy Elf Wealthy Elf!\n\n"
    "Just tell me things naturally:\n"
    "  \"slept 7.5 hrs\"\n"
    "  \"drank 1.5L water\"\n"
    "  \"gym 45 min\"\n"
    "  \"feeling good today\"\n"
    "  \"$12 lunch at toast box\"\n\n"
    "I'll sort it into your Healthy Elf or Wealthy Elf stats automatically.\n"
    "Use /status anytime to check your XP and streaks."
)

HELP = (
    "You can log:\n"
    "🩺 Health: sleep, water, workout, mood — just describe it naturally\n"
    "💸 Finance: any expense — \"$amount for what\"\n\n"
    "Commands:\n"
    "/status - your current XP, streaks, and weekly spend\n"
    "/help - this message"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username)
    await update.message.reply_text(WELCOME)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username)
    s = db.get_status(user.id)

    lines = [
        "📊 *Elf Status*",
        f"🧝 Healthy Elf XP: {s['health_xp']}",
        f"💰 Wealthy Elf XP: {s['wealth_xp']}",
        "",
        "🔥 Streaks:",
    ]
    if s["streaks"]:
        for habit, streak in s["streaks"].items():
            lines.append(f"  {habit}: {streak} day(s)")
    else:
        lines.append("  none yet — log something!")

    lines.append("")
    lines.append("💸 Last 7 days spend:")
    if s["week_spend"]:
        for row in s["week_spend"]:
            lines.append(f"  {row['category']}: ${row['total']:.2f}")
    else:
        lines.append("  no expenses logged yet")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username)
    text = update.message.text

    parsed = parse_log_message(text)

    if parsed["type"] == "health":
        streak = db.add_health_log(user.id, parsed["habit_type"], parsed["value"])
        await update.message.reply_text(
            f"🧝 Logged {parsed['habit_type']}: {parsed['value']}\n"
            f"🔥 Streak: {streak} day(s) — +10 Health XP"
        )

    elif parsed["type"] == "finance":
        db.add_finance_log(
            user.id, parsed["amount"], parsed["category"], parsed.get("note")
        )
        note_str = f" ({parsed['note']})" if parsed.get("note") else ""
        await update.message.reply_text(
            f"💰 Logged ${parsed['amount']:.2f} — {parsed['category']}{note_str}\n"
            f"+10 Wealth XP"
        )

    else:
        await update.message.reply_text(
            "Hmm, I couldn't tell if that was a health or finance log. "
            "Try something like \"slept 7 hrs\" or \"$12 lunch\". Use /help for examples."
        )


def build_app():
    db.init_db()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app


if __name__ == "__main__":
    application = build_app()
    logger.info("Healthy Elf Wealthy Elf bot starting (polling mode)...")
    application.run_polling()
