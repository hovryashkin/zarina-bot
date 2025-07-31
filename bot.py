import logging
import os
import time
from dotenv import load_dotenv
import gspread
import openai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Настройка OpenRouter API
openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_type = "openai"

# Авторизация в Google Sheets
gc = gspread.service_account(filename="/etc/secrets/credentials.json")
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

# Глобальная переменная для хранения последнего вопроса
last_question = {}

async def generate_question() -> str:
    response = openai.ChatCompletion.create(
        model="meta-llama/llama3-70b-instruct",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты бот, который задает вопросы девушке, чтобы получше ее узнать. "
                    "Задай один короткий, интересный и личный вопрос на одну из тем: "
                    "отношения, семья, мечты, страхи, воспоминания, чувства, детство, будущее, самопознание. "
                    "задавай вопросы исключительно на русском языке и без ошибок. "
                    "Без пояснений и фраз типа 'вот вопрос'. Только вопрос."
                ),
            },
            {"role": "user", "content": "Задай один вопрос."},
        ],
        temperature=0.8,
        max_tokens=60,
    )
    return response.choices[0].message["content"].strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = await generate_question()
    last_question[user_id] = question
    await update.message.reply_text(question)

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    response = update.message.text.strip()
    question = last_question.get(user_id, "Неизвестный вопрос")

    sheet.append_row([
        str(user_id),
        username,
        question,
        response,
        time.strftime("%Y-%m-%d %H:%M:%S")
    ])

    new_question = await generate_question()
    last_question[user_id] = new_question
    await update.message.reply_text(new_question)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    logging.info("🤖 Бот запущен и ждёт сообщений...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
