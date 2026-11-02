import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import init_db, upsert_user

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Регистрируем пользователя в базе
    upsert_user(user_id)
    await update.message.reply_text("Привет! Бот успешно запущен и работает 24/7 на Render. 🚀")

def main():
    # Инициализируем базу данных (создаем таблицы при первом запуске)
    init_db()

    if not TOKEN:
        logging.error("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")
        return

    # Запуск бота
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    logging.info("Бот запущен и ожидает сообщения...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
