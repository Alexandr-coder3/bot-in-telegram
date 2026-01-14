from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)
import datetime

# ========= НАЛАШТУВАННЯ =========
TOKEN = "8094754063:AAHNoaIApq1K_vVHTsKk_R_24eLVWuD_1oU"
ADMIN_ID = 7695504748
CONTACT_TG = "@MrCapitalist3"
CONTACT_PHONE = "+380669367611"

# Стан замовлення
SELECT_PACKAGE, GET_PHONE, GET_QUANTITY, GET_COMMENT = range(4)
user_order = {}
orders_enabled = True
orders_count = 0

# ========= ПАКЕТИ =========
PACKAGES = {
    "basic": ("🟢 Базовий", "1800 грн"),
    "standard": ("🔵 Стандарт", "2500 грн"),
    "pro": ("🔥 PRO", "4000 грн")
}

# ========= ВАЛІДАЦІЯ НОМЕРА =========
def validate_phone(phone: str) -> bool:
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+380") and len(phone) == 13 and phone[1:].isdigit():
        return True
    elif phone.startswith("0") and len(phone) == 10 and phone.isdigit():
        return True
    else:
        return False

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(v[0], callback_data=k)] for k,v in PACKAGES.items()]
    kb.append([InlineKeyboardButton("📩 Замовити", callback_data="order")])
    kb.append([InlineKeyboardButton("💳 Оплата", callback_data="pay")])
    kb.append([InlineKeyboardButton("💬 Як ми працюємо", callback_data="how")])
    kb.append([InlineKeyboardButton("📞 Контакти", callback_data="contacts")])

    await update.message.reply_text(
        "👋 *Вітаємо!*\n\n"
        "Ми створюємо *Telegram-ботів для бізнесу*:\n"
        "• магазини\n• прийом заявок\n• автоматизація\n\n"
        "✅ Без AI\n✅ Чесно\n\n"
        "⬇️ Оберіть дію:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return SELECT_PACKAGE

# ========= Вибір пакета =========
async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in PACKAGES:
        user_order[query.from_user.id] = {"package": query.data}
        await query.edit_message_text(
            f"Ви обрали: {PACKAGES[query.data][0]}\n\n📞 Введіть свій номер телефону (формат +380XXXXXXXXX або 0XXXXXXXXX):"
        )
        return GET_PHONE
    elif query.data == "pay":
        await query.edit_message_text(
            "💳 *Оплата:*\n\n"
            "• Передоплата 50%\n"
            "• Переказ на карту ПриватБанк:\n"
            "   ▸ 4444 5555 6666 7777 (Ім'я Прізвище)\n"
            "• Після підтвердження заявки ми продовжимо розробку",
            parse_mode="Markdown")
    elif query.data == "how":
        await query.edit_message_text(
            "💬 *Як ми працюємо:*\n\n"
            "1️⃣ Заявка\n2️⃣ Уточнення\n3️⃣ Розробка\n4️⃣ Передача\n⏱ 1–3 дні",
            parse_mode="Markdown"
        )
    elif query.data == "contacts":
        await query.edit_message_text(
            f"📞 *Контакти:*\nTelegram: {CONTACT_TG}\nТел: {CONTACT_PHONE}",
            parse_mode="Markdown"
        )
    elif query.data == "order":
        await query.edit_message_text("📩 Виберіть пакет / натисніть на кнопку пакету")
        return SELECT_PACKAGE

# ========= Отримання номера телефону =========
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    phone = update.message.text

    if not validate_phone(phone):
        await update.message.reply_text(
            "❌ Невірний номер. Будь ласка, введіть номер у форматі +380XXXXXXXXX або 0XXXXXXXXX"
        )
        return GET_PHONE

    user_order[user_id]["phone"] = phone
    await update.message.reply_text("🧮 Введіть кількість / деталі замовлення:")
    return GET_QUANTITY

# ========= Отримання кількості / деталей =========
async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_order[user_id]["quantity"] = update.message.text
    await update.message.reply_text("📝 Додаткові побажання (якщо є, або напишіть 'Ні'):")
    return GET_COMMENT

# ========= Отримання коментаря та відправка адміну =========
async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orders_count
    user_id = update.message.from_user.id
    user_order[user_id]["comment"] = update.message.text
    orders_count += 1

    data = user_order[user_id]
    user = update.message.from_user

    # Кнопка "Написати клієнту"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✍️ Написати клієнту", url=f"https://t.me/{user.username}")]])

    admin_text = (
        f"📩 *НОВА ЗАЯВКА #{orders_count}*\n\n"
        f"👤 Клієнт: {user.first_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Username: @{user.username if user.username else 'немає'}\n"
        f"📦 Пакет: {PACKAGES[data['package']][0]} ({PACKAGES[data['package']][1]})\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🧮 Кількість / деталі: {data['quantity']}\n"
        f"📝 Коментар: {data['comment']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown", reply_markup=kb)

    # Збереження у файл
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("orders.txt", "a", encoding="utf-8") as f:
        f.write(f"{now} | {user.id} | {user.first_name} | {PACKAGES[data['package']][0]} | {data['phone']} | {data['quantity']} | {data['comment']}\n")

    # Відповідь клієнту
    await update.message.reply_text(
        "✅ Дякуємо! Ваша заявка прийнята. Менеджер звʼяжеться з вами найближчим часом."
    )
    return ConversationHandler.END

# ========= Відміна =========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Замовлення скасовано.")
    return ConversationHandler.END

# ========= Адмін-команди =========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text(f"📊 Кількість замовлень: {orders_count}")

async def orders_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orders_enabled
    if update.message.from_user.id == ADMIN_ID:
        orders_enabled = True
        await update.message.reply_text("✅ Прийом замовлень увімкнено")

async def orders_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global orders_enabled
    if update.message.from_user.id == ADMIN_ID:
        orders_enabled = False
        await update.message.reply_text("⛔ Прийом замовлень вимкнено")

# ========= ГОЛОВНА =========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PACKAGE: [CallbackQueryHandler(select_package)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity)],
            GET_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", lambda u,c: u.message.reply_text(
        "ℹ️ Використовуйте /start для початку замовлення"
    )))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("on", orders_on))
    app.add_handler(CommandHandler("off", orders_off))

    print("🔥 PREMIUM Бот запущений")
    app.run_polling()

if __name__ == "__main__":
    main()