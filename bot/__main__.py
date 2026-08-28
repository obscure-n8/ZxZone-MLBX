import asyncio
import logging
from pyrogram import Client, idle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    from bot.config import Config
    
    bot = Client(
        "ZxZone-MLBX",
        api_id=Config.TELEGRAM_API,
        api_hash=Config.TELEGRAM_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="bot/plugins")
    )
    
    await bot.start()
    logger.info("Bot started!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
