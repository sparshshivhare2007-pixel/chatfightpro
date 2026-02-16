from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


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

    # Add Updates button only if channel exists
    if updates_channel:
        keyboard.append(
            [InlineKeyboardButton("📢 Updates", url=updates_channel)]
        )

    await update.message.reply_text(
        "🤖 <b>Welcome!</b>\n\n"
        "This bot counts group messages and creates leaderboards.\n"
        "Add me to a group and start chatting.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
