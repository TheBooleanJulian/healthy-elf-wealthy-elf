"""
Uses the Claude API to turn a free-text Telegram message into a structured
log entry: either a health log (sleep/water/workout/mood) or a finance log
(amount/category/note).

Kept deliberately simple for MVP: one API call, strict JSON-only response,
manual parse with a safe fallback to "unrecognized" so the bot can ask the
user to rephrase instead of crashing.
"""

import json
import anthropic

from config import ANTHROPIC_API_KEY, HEALTH_HABIT_TYPES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""You classify a short message from a habit + finance tracking bot
called "Healthy Elf Wealthy Elf". The message is either:

1. A HEALTH log about one of: {", ".join(HEALTH_HABIT_TYPES)}
2. A FINANCE log about a expense (amount spent + category)
3. UNRECOGNIZED if it's neither (e.g. small talk, a command, gibberish)

Respond with ONLY a raw JSON object, no markdown fences, no preamble. Schema:

For health:
{{"type": "health", "habit_type": "sleep|water|workout|mood", "value": "<short human-readable value, e.g. '7.5 hours', '1.5L', 'yes', 'good'>"}}

For finance:
{{"type": "finance", "amount": <number>, "category": "<short lowercase category, e.g. food, transport, shopping, bills>", "note": "<short note or null>"}}

For unrecognized:
{{"type": "unrecognized"}}

Examples:
"slept 7.5 hrs" -> {{"type": "health", "habit_type": "sleep", "value": "7.5 hours"}}
"drank 2L water today" -> {{"type": "health", "habit_type": "water", "value": "2L"}}
"gym for 45 min" -> {{"type": "health", "habit_type": "workout", "value": "45 min"}}
"feeling great today" -> {{"type": "health", "habit_type": "mood", "value": "great"}}
"$12 lunch at toast box" -> {{"type": "finance", "amount": 12, "category": "food", "note": "lunch at toast box"}}
"spent 45 on grab rides" -> {{"type": "finance", "amount": 45, "category": "transport", "note": "grab rides"}}
"hey how are you" -> {{"type": "unrecognized"}}
"""


def parse_log_message(text: str) -> dict:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        if parsed.get("type") not in ("health", "finance", "unrecognized"):
            return {"type": "unrecognized"}
        return parsed
    except Exception:
        return {"type": "unrecognized"}
