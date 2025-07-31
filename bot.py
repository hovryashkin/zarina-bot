import os
from dotenv import load_dotenv
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import gspread
from datetime import datetime

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Google Sheets

sheet = gc.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
gc = gspread.service_account(filename="/etc/secrets/credentials.json")
# Временное хранилище вопросов
pending_questions = {}

# Генерация вопроса
def generate_question():
    prompt = (
        "Ты бот, который задает вопросы девушке, чтобы получше ее узнать. "
        "Задай один короткий, интересный и личный вопрос на одну из тем: "
        "отношения, семья, мечты, страхи, воспоминания, чувства, детство, будущее, самопознание. "
        "задавай вопросы исключтельно на русском языке и без ошибок. "
        "Без пояснений и фраз типа 'вот вопрос'. Только вопрос."
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 50
    }

    response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "⚠️ Не удалось сгенерировать вопрос."

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id_str = str(user.id)
    username = user.username or ""
    name = user.first_name
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = update.message.text

    # Если у пользователя уже есть несохранённый вопрос — записываем его + ответ
    if user.id in pending_questions:
        question_data = pending_questions.pop(user.id)
        sheet.append_row([
            user_id_str,
            username,
            name,
            question_data["question"],
            message,
            question_data["timestamp"],
            now
        ])

    # Генерируем новый вопрос
    question = generate_question()
    question_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pending_questions[user.id] = {
        "question": question,
        "timestamp": question_time
    }

    await update.message.reply_text(question)

# Запуск
if __name__ == "__main__":
    print("🤖 Бот запущен и ждёт сообщений...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
