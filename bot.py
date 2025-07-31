import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/etc/secrets/credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Инициализация OpenRouter клиента
openai = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Генерация вопроса
async def generate_question():
    response = openai.chat.completions.create(
        model="mistralai/mixtral-8x7b-instruct",
        messages=[
            {"role": "system", "content": "Ты заботливый парень, который задаёт один короткий, но глубокий личный вопрос на русском языке. Не объясняй вопрос, просто задай его."}
        ]
    )
    return response.choices[0].message.content.strip()

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = await generate_question()
    await update.message.reply_text(question)

# Обработка входящих сообщений (ответов Зарины)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    answer = update.message.text
    question = "Последний вопрос неизвестен"

    # Сохраняем в Google Таблицу
    sheet.append_row([user.id, user.username, question, answer])

    # Присылаем следующий вопрос
    next_question = await generate_question()
    await update.message.reply_text(next_question)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
