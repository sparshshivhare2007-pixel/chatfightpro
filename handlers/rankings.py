from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_leaderboard


async def rankings(update, context):
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Use this in a group.")
        return

    await send_leaderboard(update, context, "overall")


async def send_leaderboard(update, context, mode):
    group_id = update.effective_chat.id
    data = get_leaderboard(group_id, mode)

    text = "📈 LEADERBOARD\n\n"

    for i, (user_id, count) in enumerate(data, start=1):
        try:
            user = await context.bot.get_chat(user_id)
            if user.username:
                name = f"<a href='https://t.me/{user.username}'>{user.first_name}</a>"
            else:
                name = user.first_name
        except:
            name = "Unknown"

        text += f"{i}. {name} • {count}\n"

    keyboard = [
        [
            InlineKeyboardButton("Overall", callback_data="rank_overall"),
            InlineKeyboardButton("Today", callback_data="rank_today"),
            InlineKeyboardButton("Week", callback_data="rank_week"),
        ]
    ]

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
