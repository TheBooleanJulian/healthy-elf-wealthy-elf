"""
SQLite storage layer for Healthy Elf Wealthy Elf.

Tables:
  users         - one row per telegram user, tracks XP totals
  health_logs   - raw health log entries (sleep/water/workout/mood)
  finance_logs  - raw expense entries
  streaks       - current/longest streak per user per habit type
"""

import sqlite3
from datetime import date, datetime
from contextlib import contextmanager

from config import DB_PATH, XP_PER_HEALTH_LOG, XP_PER_FINANCE_LOG, HEALTH_HABIT_TYPES

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    health_xp INTEGER NOT NULL DEFAULT 0,
    wealth_xp INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS health_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    habit_type TEXT NOT NULL,   -- sleep | water | workout | mood
    value TEXT NOT NULL,        -- raw value, e.g. "7.5 hours", "1.5L", "yes", "good"
    logged_at TEXT NOT NULL,    -- ISO timestamp
    log_date TEXT NOT NULL,     -- YYYY-MM-DD, used for streak/day dedupe
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS finance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT,
    logged_at TEXT NOT NULL,
    log_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS streaks (
    user_id INTEGER NOT NULL,
    habit_type TEXT NOT NULL,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_logged_date TEXT,
    PRIMARY KEY (user_id, habit_type)
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def ensure_user(telegram_id: int, username: str | None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO users (telegram_id, username, created_at)
               VALUES (?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username""",
            (telegram_id, username, datetime.utcnow().isoformat()),
        )


def _bump_streak(conn, user_id: int, habit_type: str, log_date: str):
    row = conn.execute(
        "SELECT * FROM streaks WHERE user_id=? AND habit_type=?",
        (user_id, habit_type),
    ).fetchone()

    today = date.fromisoformat(log_date)

    if row is None:
        conn.execute(
            """INSERT INTO streaks (user_id, habit_type, current_streak, longest_streak, last_logged_date)
               VALUES (?, ?, 1, 1, ?)""",
            (user_id, habit_type, log_date),
        )
        return 1

    last = row["last_logged_date"]
    current = row["current_streak"]
    longest = row["longest_streak"]

    if last == log_date:
        # already logged today, streak unchanged
        new_current = current
    else:
        last_date = date.fromisoformat(last) if last else None
        if last_date and (today - last_date).days == 1:
            new_current = current + 1
        else:
            new_current = 1  # streak broken or first-ever gap, restart

    new_longest = max(longest, new_current)
    conn.execute(
        """UPDATE streaks SET current_streak=?, longest_streak=?, last_logged_date=?
           WHERE user_id=? AND habit_type=?""",
        (new_current, new_longest, log_date, user_id, habit_type),
    )
    return new_current


def add_health_log(user_id: int, habit_type: str, value: str, when: datetime | None = None) -> int:
    when = when or datetime.utcnow()
    log_date = when.date().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO health_logs (user_id, habit_type, value, logged_at, log_date)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, habit_type, value, when.isoformat(), log_date),
        )
        conn.execute(
            "UPDATE users SET health_xp = health_xp + ? WHERE telegram_id=?",
            (XP_PER_HEALTH_LOG, user_id),
        )
        streak = _bump_streak(conn, user_id, habit_type, log_date)
        return streak


def add_finance_log(user_id: int, amount: float, category: str, note: str | None, when: datetime | None = None):
    when = when or datetime.utcnow()
    log_date = when.date().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO finance_logs (user_id, amount, category, note, logged_at, log_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, amount, category, note, when.isoformat(), log_date),
        )
        conn.execute(
            "UPDATE users SET wealth_xp = wealth_xp + ? WHERE telegram_id=?",
            (XP_PER_FINANCE_LOG, user_id),
        )


def get_status(user_id: int) -> dict:
    with get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE telegram_id=?", (user_id,)
        ).fetchone()
        streaks = conn.execute(
            "SELECT * FROM streaks WHERE user_id=?", (user_id,)
        ).fetchall()
        week_spend = conn.execute(
            """SELECT category, SUM(amount) as total FROM finance_logs
               WHERE user_id=? AND log_date >= date('now', '-7 days')
               GROUP BY category ORDER BY total DESC""",
            (user_id,),
        ).fetchall()

    return {
        "health_xp": user["health_xp"] if user else 0,
        "wealth_xp": user["wealth_xp"] if user else 0,
        "streaks": {row["habit_type"]: row["current_streak"] for row in streaks},
        "week_spend": [{"category": r["category"], "total": r["total"]} for r in week_spend],
    }
