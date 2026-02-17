import logging
import html
import random

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
from database import (
    increment_message,
    get_leaderboard,
    get_total_group_messages,
    add_event_points
)

from handlers.topusers import topusers, global_buttons
from handlers.mytop import mytop, mytop_buttons
from handlers.topgroups import topgroups, topgroups_buttons
from handlers.broadcast import broadcast
from handlers.logger import log_start, log_bot_status


# =========================
# BASIC SETUP
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

Config.validate()
app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

START_IMAGE = "https://files.catbox.moe/sscl7n.jpg"
SUPPORT_LINK = Config.SUPPORT_GROUP

active_events = {}


# =========================
# START
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
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Your stats", callback_data="stats")
        ]
    ]

    await update.message.reply_photo(
        photo=START_IMAGE,
        caption="🤖 <b>Welcome!</b>\n\nBot counts messages & shows rankings.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SETTINGS
# =========================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    keyboard = [
        [InlineKeyboardButton("💬 Support", url=SUPPORT_LINK)],
        [InlineKeyboardButton("⬅ Back", callback_data="back_home")]
    ]

    await query.edit_message_caption(
        caption="⚙️ <b>Settings</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass
    await start(update, context)


# =========================
# MESSAGE COUNTER
# =========================

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if update.message.chat.type not in ["group", "supergroup"]:
        return

    increment_message(
        update.message.from_user.id,
        update.message.chat.id
    )


# =========================
# LEADERBOARD SYSTEM
# =========================

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use inside group.")
        return

    await send_leaderboard(update, context, "overall")


async def send_leaderboard(update, context, mode):

    group_id = update.effective_chat.id
    data = get_leaderboard(group_id, mode)
    total_messages = get_total_group_messages(group_id, mode)

    text = "📈 <b>LEADERBOARD</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    if not data:
        text += "No data yet.\n"
    else:
        for i, (user_id, count) in enumerate(data, start=1):
            try:
                user = await context.bot.get_chat(user_id)
                name = f"<a href='tg://user?id={user_id}'>{html.escape(user.full_name)}</a>"
            except:
                name = "Unknown"

            medal = medals[i - 1] if i <= 3 else f"{i}."
            text += f"{medal} {name} • {count:,}\n"

    text += f"\n📨 <b>Total messages:</b> {total_messages:,}"

    keyboard = [[
        InlineKeyboardButton(
            "Overall ✅" if mode == "overall" else "Overall",
            callback_data="rank_overall"
        ),
        InlineKeyboardButton(
            "Today ✅" if mode == "today" else "Today",
            callback_data="rank_today"
        ),
        InlineKeyboardButton(
            "Week ✅" if mode == "week" else "Week",
            callback_data="rank_week"
        ),
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except:
            await update.callback_query.message.reply_text(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )


async def ranking_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except:
        pass

    if query.data == "rank_today":
        await send_leaderboard(update, context, "today")
    elif query.data == "rank_week":
        await send_leaderboard(update, context, "week")
    else:
        await send_leaderboard(update, context, "overall")


# =========================
# HANDLERS
# =========================

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rankings", rankings))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("mytop", mytop))
app.add_handler(CommandHandler("topusers", topusers))
app.add_handler(CommandHandler("topgroups", topgroups))

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
# RUN
# =========================

if __name__ == "__main__":
    app.run_polling(drop_pending_updates=True)
