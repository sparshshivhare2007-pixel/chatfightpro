import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    BOT_USERNAME = os.getenv("BOT_USERNAME")
    UPDATES_CHANNEL = os.getenv("UPDATES_CHANNEL")
    DATABASE_URL = os.getenv("DATABASE_URL", "chatfight.db")

    @staticmethod
    def validate():
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN missing in .env")
