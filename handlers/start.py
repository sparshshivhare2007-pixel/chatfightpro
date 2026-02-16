from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("➕ Add me in a group",
         url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Your stats", callback_data="stats")
        ],
        [InlineKeyboardButton("📢 Updates", url=context.bot_data.get("updates_channel"))]
    ]

    await update.message.reply_text(
        "🤖 Welcome! This bot counts group messages and creates rankings.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
