import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import (
    get_leaderboard,
    get_user_overall_stats,
    get_user_today_stats,
    get_user_week_stats,
)


async def mytop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_mytop(update, context, "overall")


async def send_mytop(update, context, mode):
    user_id = update.effective_user.id
    chat = update.effective_chat

    # ===== GROUP MODE =====
    if chat.type in ["group", "supergroup"]:
        group_id = chat.id
        leaderboard = get_leaderboard(group_id, mode)

        rank = None
        total = 0

        for i, (uid, count) in enumerate(leaderboard, start=1):
            if uid == user_id:
                rank = i
                total = count
                break

        if rank is None:
            total = 0
            rank_text = "Not ranked yet"
        else:
            rank_text = f"{rank}"

        text = (
            "📊 <b>MY STATS</b>\n\n"
            f"🏆 <b>Your rank:</b> {rank_text}\n"
            f"📤 <b>Messages:</b> {total:,}\n"
        )

    # ===== DM MODE (GLOBAL) =====
    else:
        if mode == "today":
            messages, groups = get_user_today_stats(user_id)
        elif mode == "week":
            messages, groups = get_user_week_stats(user_id)
        else:
            messages, groups = get_user_overall_stats(user_id)

        text = (
            "📊 <b>YOUR STATS</b>\n\n"
            f"📤 <b>Messages:</b> {messages:,}\n"
            f"👥 <b>Active groups:</b> {groups}\n"
        )

    # ===== BUTTONS WITH GREEN TICK =====
    keyboard = [
        [
            InlineKeyboardButton(
                "Overall ✅" if mode == "overall" else "Overall",
                callback_data="my_overall"
            ),
            InlineKeyboardButton(
                "Today ✅" if mode == "today" else "Today",
                callback_data="my_today"
            ),
            InlineKeyboardButton(
                "Week ✅" if mode == "week" else "Week",
                callback_data="my_week"
            ),
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


async def mytop_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "my_today":
        await send_mytop(update, context, "today")
    elif query.data == "my_week":
        await send_mytop(update, context, "week")
    else:
        await send_mytop(update, context, "overall")
