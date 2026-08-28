from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Repo", url="https://github.com/obscure-n8/ZxZone-MLBX"),
            InlineKeyboardButton("Channel", url="https://t.me/zxzoneupdates")
        ]
    ])
    
    await message.reply_text(
        f"Welcome {user.first_name}!\n\n"
        "Powered By ZxZone Hub",
        reply_markup=keyboard
    )
