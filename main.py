"""
FastAPI wrapper so the bot can run in webhook mode on Zeabur instead of
polling. Zeabur gives you a public URL — point Telegram's setWebhook at
POST /telegram/webhook.

For local dev, just run `python bot.py` directly (polling mode) instead.
"""

from fastapi import FastAPI, Request
from telegram import Update
import uvicorn
import os

from bot import build_app

app = FastAPI(title="Healthy Elf Wealthy Elf")
telegram_app = build_app()


@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
    await telegram_app.start()


@app.on_event("shutdown")
async def shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()


@app.get("/")
async def health_check():
    return {"status": "ok", "bot": "healthy-elf-wealthy-elf"}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
