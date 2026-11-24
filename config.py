import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DB_PATH = os.environ.get("DB_PATH", "healthy_elf_wealthy_elf.db")

# XP awarded per action (MVP: flat values, tune later)
XP_PER_HEALTH_LOG = 10
XP_PER_FINANCE_LOG = 10

# Habit types tracked for streaks
HEALTH_HABIT_TYPES = ("sleep", "water", "workout", "mood")
