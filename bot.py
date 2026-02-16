import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import Config
from database import increment_message, get_leaderboard

# =========================
# Basic Setup
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

Config.validate()

app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

# =========================
# /start Command
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add me in a group",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton("📈 Rankings", callback_data="rank_overall")
        ]
    ]

    await update.message.reply_text(
        "🤖 Welcome to ChatFight Bot!\n\n"
        "I count group messages and create leaderboards.\n"
        "Use /rankings inside a group.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# Message Counter
# =========================

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        increment_message(
            update.message.from_user.id,
            update.message.chat.id
        )

# =========================
# Rankings Command
# =========================

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this command inside a group.")
        return

    await send_leaderboard(update, context, "overall")

# =========================
# Leaderboard Sender
# =========================

async def send_leaderboard(update, context, mode):
    group_id = update.effective_chat.id
    data = get_leaderboard(group_id, mode)

    text = "📈 <b>LEADERBOARD</b>\n\n"

    if not data:
        text += "No data yet."
    else:
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, count) in enumerate(data, start=1):
            try:
                user = await context.bot.get_chat(user_id)

                if user.username:
                    name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"
                else:
                    name = user.first_name

            except:
                name = "Unknown"

            medal = medals[i - 1] if i <= 3 else f"{i}."

            text += f"{medal} {name} • {count}\n"

    keyboard = [
        [
            InlineKeyboardButton("Overall", callback_data="rank_overall"),
            InlineKeyboardButton("Today", callback_data="rank_today"),
            InlineKeyboardButton("Week", callback_data="rank_week"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

# =========================
# Button Handler
# =========================

async def ranking_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rank_today":
        await send_leaderboard(update, context, "today")
    elif query.data == "rank_week":
        await send_leaderboard(update, context, "week")
    else:
        await send_leaderboard(update, context, "overall")

# =========================
# Handlers Registration
# =========================

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rankings", rankings))
app.add_handler(CallbackQueryHandler(ranking_buttons, pattern="^rank_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))

# =========================
# Run Bot
# =========================

if __name__ == "__main__":
    app.run_polling()
