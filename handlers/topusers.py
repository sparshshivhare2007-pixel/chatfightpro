import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import get_global_leaderboard, get_total_global_messages


async def topusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_global_leaderboard(update, context, "overall")


async def send_global_leaderboard(update, context, mode):
    data = get_global_leaderboard(mode)
    total_messages = get_total_global_messages(mode)  # ✅ MODE BASED

    text = "📈 <b>GLOBAL LEADERBOARD</b> 🌍\n\n"

    if not data:
        text += "No data yet."
    else:
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

    text += f"\n📨 <b>Total messages:</b> {total_messages:,}"

    keyboard = [
        [
            InlineKeyboardButton(
                "Overall ✅" if mode == "overall" else "Overall",
                callback_data="g_overall"
            )
        ],
        [
            InlineKeyboardButton(
                "Today ✅" if mode == "today" else "Today",
                callback_data="g_today"
            ),
            InlineKeyboardButton(
                "Week ✅" if mode == "week" else "Week",
                callback_data="g_week"
            ),
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


async def global_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "g_today":
        await send_global_leaderboard(update, context, "today")
    elif query.data == "g_week":
        await send_global_leaderboard(update, context, "week")
    else:
        await send_global_leaderboard(update, context, "overall")
