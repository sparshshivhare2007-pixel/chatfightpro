import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import get_leaderboard


async def mytop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this inside a group.")
        return

    await send_mytop(update, context, "overall")


async def send_mytop(update, context, mode):
    chat = update.effective_chat
    user = update.effective_user
    group_id = chat.id
    user_id = user.id

    leaderboard = get_leaderboard(group_id, mode)

    text = "📈 <b>MY RANK</b> | 🌍\n\n"

    rank_position = None
    message_count = 0

    for i, (uid, count) in enumerate(leaderboard, start=1):
        if uid == user_id:
            rank_position = i
            message_count = count
            break

    if rank_position:
        safe_name = html.escape(user.full_name)
        text += f"{rank_position}. 👤 {safe_name} • {message_count:,}\n"
    else:
        text += "You are not ranked yet.\n"

    # ===== Buttons with green tick =====
    keyboard = [
        [
            InlineKeyboardButton(
                "Overall ✅" if mode == "overall" else "Overall",
                callback_data="my_overall"
            )
        ],
        [
            InlineKeyboardButton(
                "Today ✅" if mode == "today" else "Today",
                callback_data="my_today"
            ),
            InlineKeyboardButton(
                "Week ✅" if mode == "week" else "Week",
                callback_data="my_week"
            ),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup
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
