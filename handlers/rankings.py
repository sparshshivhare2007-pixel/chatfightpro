import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import get_leaderboard


async def rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this in a group.")
        return

    await send_leaderboard(update, context, "overall")


async def send_leaderboard(update, context, mode):
    group_id = update.effective_chat.id
    data = get_leaderboard(group_id, mode)

    text = "📈 <b>LEADERBOARD</b>\n\n"

    if not data:
        text += "No data yet."
    else:
        medals = ["🥇", "🥈", "🥉"]

        for i, item in enumerate(data, start=1):
            user_id = item[0]
            count = item[1]

            try:
                user = await context.bot.get_chat(user_id)
                safe_name = html.escape(user.full_name or "User")

                if user.username:
                    name = f"<a href='https://t.me/{user.username}'>{safe_name}</a>"
                else:
                    name = safe_name
            except Exception:
                name = "Unknown"

            medal = medals[i - 1] if i <= 3 else f"{i}."
            text += f"{medal} {name} • {count:,}\n"

    # ✅ GREEN TICK LOGIC
    keyboard = [
        [
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


async def ranking_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rank_today":
        await send_leaderboard(update, context, "today")
    elif query.data == "rank_week":
        await send_leaderboard(update, context, "week")
    else:
        await send_leaderboard(update, context, "overall")
