from pyrogram import Client, filters

@Client.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply_text(
        "**Commands:**\n"
        "/start - Start\n"
        "/help - Help\n"
        "/leech - Leech\n"
        "/mirror - Mirror"
    )
