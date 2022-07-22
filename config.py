import os
from telethon import TelegramClient
from database import DBHelper

API_ID: int = int(os.getenv("API_ID"))
API_HASH: str = os.getenv("API_HASH")
BOT_TOKEN: str = os.environ.get("BOT_TOKEN")
HOURS: int = int(os.environ.get("HOURS"))
ADMIN: int = int(os.environ.get("ADMIN"))

db = DBHelper(os.getenv("DATABASE_URL"))

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


