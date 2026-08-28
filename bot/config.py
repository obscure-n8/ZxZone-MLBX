import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    TELEGRAM_API = int(os.getenv("TELEGRAM_API", "0"))
    TELEGRAM_HASH = os.getenv("TELEGRAM_HASH", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    DATABASE_URL = os.getenv("DATABASE_URL", "")
