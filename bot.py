import asyncio
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

# Загружаем переменные из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Обработчик входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text(f"Ты написал: {user_message}")

# Основная функция
async def main():
    # Создание приложения с токеном
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Добавление обработчика
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    print("Бот запущен")
    await app.run_polling()

# Запуск
if __name__ == '__main__':
    asyncio.run(main())
