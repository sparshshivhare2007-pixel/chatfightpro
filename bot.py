import logging
import html
import random
import asyncio

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
# Basic Setup
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

Config.validate()

app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

START_IMAGE = "https://files.catbox.moe/sscl7n.jpg"
SUPPORT_LINK = Config.SUPPORT_GROUP

# =========================
# EVENT STORAGE
# =========================

active_events = {}  # group_id: correct_answer


# =========================
# AUTO EVENT LOOP (2 HOURS)
# =========================

async def auto_event_loop(app):
    await app.bot.wait_until_ready()

    while True:
        await asyncio.sleep(7200)  # 2 hours

        for chat in await app.bot.get_my_commands():
            pass

        # Send event to all groups stored in DB
        # Simple version: event triggers when bot receives message
        # (To keep it stable for VPS)


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

    text = (
        "🤖 <b>Welcome!</b>\n\n"
        "This bot counts group messages, creates rankings "
        "and rewards active users."
    )

    await update.message.reply_photo(
        photo=START_IMAGE,
        caption=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SETTINGS
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
# MESSAGE COUNTER + EVENT CHECK
# =========================

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if update.message.chat.type not in ["group", "supergroup"]:
        return

    user_id = update.message.from_user.id
    group_id = update.message.chat.id

    # Count normal message
    increment_message(user_id, group_id)

    # Check active event
    if group_id in active_events:
        try:
            if int(update.message.text.strip()) == active_events[group_id]:

                # Reward
                add_event_points(user_id, group_id, 20)

                await update.message.reply_text(
                    f"🎉 {update.message.from_user.mention_html()} won the event!\n"
                    f"🏆 +20 Event Points!",
                    parse_mode="HTML"
                )

                await update.message.reply_reaction("🔥")

                del active_events[group_id]

        except:
            pass


# =========================
# MANUAL EVENT TRIGGER
# =========================

async def event(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    group_id = update.effective_chat.id

    a = random.randint(5, 20)
    b = random.randint(5, 20)

    answer = a + b
    active_events[group_id] = answer

    await update.message.reply_text(
        f"🎯 <b>ChatFight Event!</b>\n\n"
        f"⚡ Solve Fast & Win 20 Points!\n\n"
        f"🧮 {a} + {b} = ?",
        parse_mode="HTML"
    )


# =========================
# GROUP LEADERBOARD
# =========================

async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this command inside a group.")
        return

    await send_group_leaderboard(update, context, "overall")


async def send_group_leaderboard(update, context, mode):

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
                safe_name = html.escape(user.full_name or "User")
                name = f"<a href='tg://user?id={user_id}'>{safe_name}</a>"
            except:
                name = "Unknown"

            medal = medals[i - 1] if i <= 3 else f"{i}."
            text += f"{medal} {name} • {count:,}\n"

    text += f"\n📨 <b>Total messages:</b> {total_messages:,}"

    keyboard = [[
        InlineKeyboardButton("Overall", callback_data="rank_overall"),
        InlineKeyboardButton("Today", callback_data="rank_today"),
        InlineKeyboardButton("Week", callback_data="rank_week"),
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


# =========================
# HANDLERS
# =========================

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rankings", rankings))
app.add_handler(CommandHandler("event", event))  # manual trigger
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
app.add_handler(CallbackQueryHandler(global_buttons, pattern="^g_"))
app.add_handler(CallbackQueryHandler(mytop_buttons, pattern="^my_"))
app.add_handler(CallbackQueryHandler(topgroups_buttons, pattern="^tg_"))

# Counter + Event Check
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_messages))


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run_polling()
