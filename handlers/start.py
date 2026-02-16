from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


START_IMAGE = ""  
# Yaha apni banner image ka direct link daalo


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
            InlineKeyboardButton("📊 Your stats", callback_data="stats"),
        ],
    ]

    if updates_channel:
        keyboard.append(
            [InlineKeyboardButton("📢 Updates", url=updates_channel)]
        )

    text = (
        "🤖 <b>Welcome, this bot will count group messages, "
        "create rankings and give prizes to users!</b>\n\n"
        "📚 By using this bot, you consent to the processing of your data "
        "through the <a href='https://example.com/privacy'>Privacy Policy</a> "
        "and to compliance with the <a href='https://example.com/rules'>Rules</a>."
    )

    # Send photo with caption (like ChatFight)
    await update.message.reply_photo(
        photo=START_IMAGE,
        caption=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )
