import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "/etc/secrets/credentials.json")

# Настройка клиента OpenAI с OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Настройка доступа к Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Генерация вопроса через OpenRouter
async def generate_question():
    response = client.chat.completions.create(
        model="meta-llama/llama-3-70b-instruct",
        messages=[
            {"role": "system", "content": "Ты бот, который задаёт один короткий личный вопрос девушке на русском языке. Не добавляй объяснений, только вопрос."},
            {"role": "user", "content": "Задай один вопрос."}
        ],
        max_tokens=60,
        temperature=0.9
    )
    return response.choices[0].message.content.strip()

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text

    # Сохраняем ответ в Google Таблицу
    sheet.append_row([str(user.id), user.first_name, message])

    # Генерируем следующий вопрос
    question = await generate_question()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=question)

# Основная функция
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
