import random
import string
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Конфигурация бота
BOT_TOKEN = "7819954919:AAFW2jWopH1A_YoQgIhMyLWXdQfEAPAbyoo"
BOT_USERNAME = "anonvoprosy_xarmaq_bot"

# Временное хранилище; для продакшна используйте БД
user_to_code: dict[int, str] = {}         # user_id -> код
code_to_user: dict[str, int] = {}         # код -> user_id
pending_private: dict[int, int] = {}      # отправитель -> получатель


def generate_code(length: int = 6) -> str:
    """Генерирует уникальный код, который ещё не используется."""
    alphabet = string.ascii_lowercase + string.digits
    while True:
        code = ''.join(random.choices(alphabet, k=length))
        if code not in code_to_user:
            return code


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик /start:
    - Без аргументов: генерирует (или повторно показывает) постоянную реферальную ссылку.
    - С кодом: переходит в режим приёма сообщения для владельца кода.
    """
    user = update.effective_user
    args = context.args

    if args:
        code = args[0]
        recipient_id = code_to_user.get(code)
        if not recipient_id:
            await update.message.reply_text(
                "Неверная или устаревшая ссылка. Попросите получателя создать новую."
            )
            return
        pending_private[user.id] = recipient_id
        await update.message.reply_text(
            "Напишите сообщение, которое вы хотите отправить получателю."
        )
        return

    # Создаём или повторно показываем постоянную ссылку
    if user.id not in user_to_code:
        code = generate_code()
        user_to_code[user.id] = code
        code_to_user[code] = user.id
    else:
        code = user_to_code[user.id]

    link = f"https://t.me/{BOT_USERNAME}?start={code}"
    name = f"@{user.username}" if user.username else f"ID: {user.id}"
    await update.message.reply_text(
        f"Привет, {name}!\nВаша постоянная реферальная ссылка: {link}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений после перехода по реф-ссылке."""
    sender = update.effective_user
    text = update.message.text
    if sender.id in pending_private:
        recipient_id = pending_private.pop(sender.id)
        sender_name = f"@{sender.username}" if sender.username else f"ID: {sender.id}"
        message_text = (
            f"У вас новое сообщение:\n{text}\n\n(От {sender_name})"
        )
        await context.bot.send_message(chat_id=recipient_id, text=message_text)
        await update.message.reply_text("Сообщение отправлено успешно! 🎉")
    else:
        await update.message.reply_text(
            "Чтобы отправить сообщение, перейдите по реферальной ссылке получателя."
        )


def main() -> None:
    """Запуск бота без дополнительных таймаутов"""
    random.seed()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
