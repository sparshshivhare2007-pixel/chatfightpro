import logging
import html
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
from handlers.topusers import topusers, global_buttons
from handlers.mytop import mytop, mytop_buttons
from handlers.topgroups import topgroups, topgroups_buttons
from handlers.broadcast import broadcast
from handlers.logger import log_start, log_bot_status

# =========================
# Basic Setup
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

Config.validate()

app = ApplicationBuilder().token(Config.BOT_TOKEN).build()
app.bot_data["updates_channel"] = getattr(Config, "UPDATES_CHANNEL", None)

START_IMAGE = "https://files.catbox.moe/73mktq.jpg"
SUPPORT_LINK = Config.SUPPORT_GROUP

# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    updates_channel = context.bot_data.get("updates_channel")

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add me in a group",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Your stats", callback_data="stats")
        ]
    ]

    if updates_channel:
        keyboard.append(
            [InlineKeyboardButton("📢 Updates", url=updates_channel)]
        )

    text = (
        "🤖 <b>Welcome, this bot will count group messages, "
        "create rankings and give prizes to users!</b>\n\n"
        "📚 By using this bot, you consent to the processing of your data "
        "through the <b>Privacy Policy</b> and compliance with the <b>Rules</b>."
    )

    try:
        await update.message.reply_photo(
            photo=START_IMAGE,
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )

# =========================
# Settings
# =========================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💬 Support", url=SUPPORT_LINK)],
        [InlineKeyboardButton("⬅ Back", callback_data="back_home")]
    ]

    await query.edit_message_caption(
        caption="⚙️ <b>Settings</b>\n\nNeed help? Join our support group.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

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
# Group Leaderboard
# =========================

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this command inside a group.")
        return

    await send_group_leaderboard(update, context, "overall")

async def send_group_leaderboard(update, context, mode):
    group_id = update.effective_chat.id
    data = get_leaderboard(group_id, mode)

    text = "📈 <b>LEADERBOARD</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, (user_id, count) in enumerate(data, start=1):
        try:
            user = await context.bot.get_chat(user_id)
            safe_name = html.escape(user.full_name or "User")
            name = f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
        except:
            name = "Unknown"

        medal = medals[i - 1] if i <= 3 else f"{i}."
        text += f"{medal} {name} • {count:,}\n"

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
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

async def ranking_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rank_today":
        await send_group_leaderboard(update, context, "today")
    elif query.data == "rank_week":
        await send_group_leaderboard(update, context, "week")
    else:
        await send_group_leaderboard(update, context, "overall")

# =========================
# Handlers Registration
# =========================

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rankings", rankings))
app.add_handler(CommandHandler("mytop", mytop))
app.add_handler(CommandHandler("topusers", topusers))
app.add_handler(CommandHandler("topgroups", topgroups))
app.add_handler(CommandHandler("broadcast", broadcast))

# Logger
app.add_handler(CommandHandler("start", log_start), group=1)
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, log_bot_status))
app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, log_bot_status))

# Callbacks
app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
app.add_handler(CallbackQueryHandler(back_home, pattern="^back_home$"))
app.add_handler(CallbackQueryHandler(ranking_buttons, pattern="^rank_"))
app.add_handler(CallbackQueryHandler(global_buttons, pattern="^g_"))
app.add_handler(CallbackQueryHandler(mytop_buttons, pattern="^my_"))
app.add_handler(CallbackQueryHandler(topgroups_buttons, pattern="^tg_"))

# Counter
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))

# =========================
# Run
# =========================

if __name__ == "__main__":
    app.run_polling()
