import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # =========================
    # Telegram
    # =========================
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    BOT_USERNAME = os.getenv("BOT_USERNAME")
    UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL")

    # =========================
    # MongoDB
    # =========================
    MONGO_URI = os.getenv("MONGO_URI")

    # =========================
    # Validation
    # =========================
    @staticmethod
    def validate():
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN missing in .env")

        if not Config.MONGO_URI:
            raise ValueError("MONGO_URI missing in .env")
