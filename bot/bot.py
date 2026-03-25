import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

def get_public_content():
    response = requests.get(f"{API_BASE}/api/v1/content/public", timeout=20)
    response.raise_for_status()
    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Привет. Я бот Anime Platform."
    if BOT_USERNAME:
        text += f"\nUsername: @{BOT_USERNAME.lstrip('@')}"
    text += "\nКоманды: /catalog /health"
    await update.message.reply_text(text)

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get(f"{API_BASE}/health", timeout=20)
    response.raise_for_status()
    data = response.json()
    await update.message.reply_text(f"API status: {data.get('status', 'unknown')}")

async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = get_public_content()
    if not items:
        await update.message.reply_text("Опубликованного контента пока нет.")
        return
    lines = ["Каталог:"]
    for item in items[:15]:
        line = f"• {item['title']} [{item['media_type']}]"
        if item.get("tags"):
            line += f" — {item['tags']}"
        lines.append(line)
    await update.message.reply_text("\n".join(lines))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("catalog", catalog))
    app.run_polling()

if __name__ == "__main__":
    main()
