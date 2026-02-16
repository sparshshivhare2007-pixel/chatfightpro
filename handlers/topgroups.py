import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from database import get_top_groups, get_total_global_messages


async def topgroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_top_groups(update, context, "overall")


async def send_top_groups(update, context, mode):
    data, _ = get_top_groups(mode)
    total_messages = get_total_global_messages()

    text = "📈 <b>TOP GROUPS</b> 🌍\n\n"

    if not data:
        text += "No data yet."
    else:
        for i, (group_id, count) in enumerate(data, start=1):
            try:
                chat = await context.bot.get_chat(group_id)
                safe_name = html.escape(chat.title or "Group")
            except:
                safe_name = "Unknown Group"

            text += f"{i}. 👥 {safe_name} • {count:,}\n"

    text += f"\n📨 <b>Total messages:</b> {total_messages:,}"

    keyboard = [
        [
            InlineKeyboardButton(
                "Overall ✅" if mode == "overall" else "Overall",
                callback_data="tg_overall"
            )
        ],
        [
            InlineKeyboardButton("Today", callback_data="tg_today"),
            InlineKeyboardButton("Week", callback_data="tg_week"),
        ],
        [
            InlineKeyboardButton("🏳 Language", callback_data="language")
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


async def topgroups_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "tg_today":
        await send_top_groups(update, context, "today")
    elif query.data == "tg_week":
        await send_top_groups(update, context, "week")
    else:
        await send_top_groups(update, context, "overall")
