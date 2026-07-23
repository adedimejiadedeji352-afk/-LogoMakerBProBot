import os
import io
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from logo_generator import generate_logo, COLOR_SCHEMES, SHAPES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_FOR_NAME, WAITING_FOR_STYLE = range(2)
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *LogoMakerBPro*!\n\n"
        "Send me your brand or project name and I'll generate a logo for you.\n\n"
        "Type /cancel anytime to stop.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name or len(name) > 30:
        await update.message.reply_text("Please send a name between 1 and 30 characters.")
        return WAITING_FOR_NAME

    user_id = update.effective_user.id
    user_sessions[user_id] = {"name": name}

    keyboard = [
        [InlineKeyboardButton(scheme_name, callback_data=f"scheme:{scheme_name}")]
        for scheme_name in COLOR_SCHEMES.keys()
    ]
    await update.message.reply_text(
        f"Great, *{name}*! Now pick a color scheme:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return WAITING_FOR_STYLE


async def receive_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    scheme_name = query.data.split(":", 1)[1]
    if user_id not in user_sessions:
        await query.edit_message_text("Session expired. Send /start to begin again.")
        return ConversationHandler.END

    user_sessions[user_id]["scheme"] = scheme_name

    keyboard = [
        [InlineKeyboardButton(shape.capitalize(), callback_data=f"shape:{shape}")]
        for shape in SHAPES
    ]
    await query.edit_message_text(
        "Nice choice! Now pick a shape style:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return WAITING_FOR_STYLE


async def receive_shape_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_sessions or "scheme" not in user_sessions[user_id]:
        await query.edit_message_text("Session expired. Send /start to begin again.")
        return ConversationHandler.END

    shape = query.data.split(":", 1)[1]
    session = user_sessions[user_id]
    session["shape"] = shape

    await query.edit_message_text("🎨 Generating your logo...")

    image_bytes = generate_logo(
        text=session["name"],
        scheme_name=session["scheme"],
        shape=shape,
    )

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=io.BytesIO(image_bytes),
        caption=f"Here's your logo for *{session['name']}*!\n\nSend /start to make another.",
        parse_mode="Markdown",
    )

    user_sessions.pop(user_id, None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions.pop(user_id, None)
    await update.message.reply_text("Cancelled. Send /start whenever you're ready.")
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/start - Begin creating a logo\n"
        "/cancel - Cancel the current session\n"
        "/help - Show this message"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is not set. "
            "Set it in Railway's Variables tab."
        )

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_FOR_STYLE: [
                CallbackQueryHandler(receive_scheme, pattern=r"^scheme:"),
                CallbackQueryHandler(receive_shape_and_generate, pattern=r"^shape:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
