import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from datetime import datetime, timedelta, timezone

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

from database import (
    init_db, upsert_user, create_order, get_order,
    set_order_status, set_subscription, get_subscription,
    list_users
)
PORT = int(os.getenv("PORT", 10000))

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    httpd.serve_forever()
    
TOKEN ="9096858769:AAH3H6ZwldzbdGVy6FBGQc1ECRMyalFqd4s"
ADMIN_ID =8288073323
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@cudehqrrrt")
SUPPORT_URL = "https://t.me/cudehqrrrt"

MENU = ReplyKeyboardMarkup(
    [
        ["📨 Отправить предложение", "🛍 Купить"],
        ["👤 Админ", "🆘 Поддержка"],
    ],
    resize_keyboard=True
)

RECIPIENT, NFT_LINK, PRICE, PREVIEW = range(4)
TARIFFS = {
    "week": ("WEEK", 7, "5 TON"),
    "month": ("MONTH", 30, "15 TON"),
    "forever": ("FOREVER", None, "20 TON"),
}

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("nft-offer-bot")

import sqlite3
try:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription = 'active' WHERE user_id = 8288073323")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, subscription) VALUES (8288073323, 'active')")
    conn.commit()
    conn.close()
except Exception as e:
    print("Ошибка активации админа:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user.id, user.username or "")
    await update.message.reply_text(
        "💎 Добро пожаловать!\nВыберите нужный раздел:",
        reply_markup=MENU
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Действие отменено.", reply_markup=MENU)
    return ConversationHandler.END


async def has_access(user_id: int) -> bool:
    sub = get_subscription(user_id)
    if not sub:
        return False
    if sub["plan"] == "forever":
        return sub["active"]
    if not sub["expires_at"]:
        return False
    expires = datetime.fromisoformat(sub["expires_at"])
    return bool(sub["active"] and expires > datetime.now(timezone.utc))


async def begin_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 8288073323 and not await has_access(update.effective_user.id):

        await update.message.reply_text(
            "Для отправки предложений нужна активная подписка.\n"
            "Откройте раздел «🛍 Купить».",
            reply_markup=MENU
        )
        return ConversationHandler.END
    await update.message.reply_text("Введите числовой Telegram ID получателя:")
    return RECIPIENT


async def get_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not value.isdigit():
        await update.message.reply_text("Нужен числовой Telegram ID. Попробуйте ещё раз:")
        return RECIPIENT
    context.user_data["recipient_id"] = int(value)
    await update.message.reply_text("Пришлите HTTPS-ссылку на NFT:")
    return NFT_LINK


async def get_nft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    if not ("t.me/" in link or "http" in link) or len(link) >= 1000:
        
        
        await update.message.reply_text("Нужна корректная HTTPS-ссылка. Попробуйте ещё раз:")
        return NFT_LINK
    context.user_data["nft_link"] = link
    await update.message.reply_text("Укажите цену в целых Telegram Stars:")
    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = update.message.text.strip()
    if not value.isdigit() or int(value) < 1:
        await update.message.reply_text("Цена должна быть положительным целым числом.")
        return PRICE
    context.user_data["price"] = int(value)
    preview = (
        "💎 NFT OFFER\n\n"
        f"🎁 NFT: {context.user_data['nft_link']}\n"
        f"💰 Цена: {context.user_data['price']} ⭐\n"
        f"👤 Получатель ID: {context.user_data['recipient_id']}\n\n"
        "Проверьте данные перед отправкой."
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Подтвердить", callback_data="order_confirm"),
        InlineKeyboardButton("✖️ Отмена", callback_data="order_cancel"),
    ]])
    await update.message.reply_text(preview, reply_markup=keyboard)
    return PREVIEW

async def preview_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "order_cancel":
        context.user_data.clear()
        await query.edit_message_text("Предложение отменено.")
        return ConversationHandler.END

    elif query.data == "order_confirm":
        owner_id = query.from_user.id
        recipient_id = context.user_data.get("recipient_id")
        nft_link = context.user_data.get("nft_link")
        price = context.user_data.get("price")

        if not all([recipient_id, nft_link, price]):
            await query.edit_message_text("Не удалось восстановить данные ордера. Начните заново.")
            return ConversationHandler.END

        order_id = create_order(owner_id, recipient_id, nft_link, price)

        # Реальная отправка сообщения получателю
        await context.bot.send_message(
            chat_id=recipient_id,
            text=f"📦 Вам поступило новое предложение по NFT!\nСсылка: {nft_link}\nЦена: {price}"
        )

        await query.edit_message_text(f"Ордер #{order_id} успешно сохранён и отправлен!")
        context.user_data.clear()
        return ConversationHandler.END




async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 WEEK — 7 дней — 5 TON", callback_data="buy_week")],
        [InlineKeyboardButton("💎 MONTH — 30 дней — 15 TON", callback_data="buy_month")],
        [InlineKeyboardButton("🏆 FOREVER — навсегда — 20 TON", callback_data="buy_forever")],
    ])
    await update.message.reply_text("Выберите тариф:", reply_markup=kb)


async def buy_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.removeprefix("buy_")
    title, days, price = TARIFFS[key]
    address = os.environ.get("TON_RECEIVE_ADDRESS", "")
    text = (
        f"💎 Тариф: {title}\n"
        f"⏳ Срок: {'навсегда' if days is None else str(days) + ' дней'}\n"
        f"💰 Стоимость: {price}\n\n"
        f"TON-адрес:\n{address or 'Адрес не настроен администратором'}\n\n"
        f"После оплаты свяжитесь с администратором: {ADMIN_USERNAME}\n"
        "Активация — только после самостоятельной проверки поступления средств "
        "администратором. Не отправляйте никому seed-фразы или приватные ключи. "
        "Финансовые действия несовершеннолетним следует проводить только "
        "с участием доверенного взрослого."
    )
    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("👤 Связаться с администратором", url=SUPPORT_URL)
        ]])
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        await update.message.reply_text("Раздел недоступен.")
        return
    users = list_users()
    await update.message.reply_text(
        f"👑 Админ-панель\nПользователей: {len(users)}\n\n"
        "Команды:\n"
        "/grant USER_ID week|month|forever\n"
        "/revoke USER_ID\n"
        "/users"
    )


async def grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    if len(context.args) != 2:
        await update.message.reply_text("Формат: /grant USER_ID week|month|forever")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER_ID должен быть числом.")
        return
    plan = context.args[1].lower()
    if plan not in TARIFFS:
        await update.message.reply_text("Тариф: week, month или forever.")
        return
    _, days, _ = TARIFFS[plan]
    expires = None if days is None else (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    set_subscription(user_id, plan, expires, True)
    await update.message.reply_text(f"Подписка {plan} активирована для {user_id}.")


async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Формат: /revoke USER_ID")
        return
    set_subscription(int(context.args[0]), "none", None, False)
    await update.message.reply_text("Подписка отозвана.")


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return
    users = list_users()
    lines = [f"{u['user_id']} — @{u['username'] or 'без username'}" for u in users[:50]]
    await update.message.reply_text("\n".join(lines) if lines else "Пользователей пока нет.")


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 Поддержка\nСвязаться с администратором:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Написать администратору", url=SUPPORT_URL)
        ]])
    )


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🛍 Купить":
        await buy(update, context)
    elif text == "👤 Админ":
        await admin_panel(update, context)
    elif text == "🆘 Поддержка":
        await support(update, context)
    elif text == "📨 Отправить предложение":
        await begin_order(update, context)
    else:
        await update.message.reply_text("Выберите раздел в меню.", reply_markup=MENU)


def main():
    if not TOKEN:
        raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в Replit Secrets.")
    if ADMIN_ID == 0:
        raise RuntimeError("Не задан ADMIN_ID в Replit Secrets.")
    
    init_db()
    threading.Thread(target=run_web_server, daemon=True).start()
    
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )
    




    order_flow = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📨 Отправить предложение$"), begin_order)],
        states={
            RECIPIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipient)],
            NFT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nft)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            PREVIEW: [CallbackQueryHandler(preview_action, pattern="^order_(confirm|cancel)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("grant", grant))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(order_flow)
    app.add_handler(CallbackQueryHandler(buy_choice, pattern="^buy_(week|month|forever)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    log.info("Bot polling started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
