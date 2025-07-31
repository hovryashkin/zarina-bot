import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Загрузка переменных из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SPREADSHEET_ID = "1hYCwwssr9aTxSUs4atU2IjnaNKaGVoj5UhjvcY2I0xA"

# Настройка Google Таблицы
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = '/etc/secrets/credentials.json'  # путь на Render
creds = ServiceAccountCredentials.from_json_keyfile_name(
    '/etc/secrets/credentials.json',
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Настройка OpenRouter (через OpenAI совместимый интерфейс)
openai = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Хендлер старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Зарина 💖 Я хочу узнать тебя получше. Поехали!")

    # Генерация первого вопроса
    question = await generate_question()
    await update.message.reply_text(question)

# Генерация вопроса
async def generate_question():
    response = openai.chat.completions.create(
        model="meta-llama/llama-3-70b-instruct",
        messages=[
            {"role": "system", "content": "Ты создаёшь короткие, личные и интересные вопросы для девушки, которая отвечает на них в телеграм-боте. Пиши на русском языке, без объяснений, просто вопрос."},
            {"role": "user", "content": "Задай 1 вопрос."}
        ]
    )
    return response.choices[0].message.content.strip()

# Хендлер сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Сохраняем ответ в Google Таблицу
    sheet.append_row([str(user_id), username, user_message])

    # Генерируем следующий вопрос
    question = await generate_question()
    await update.message.reply_text(question)

# Основная функция
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
