from pyrogram import Client, filters

@Client.on_message(filters.command("mirror"))
async def mirror_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /mirror <url>")
        return
    
    await message.reply_text("Mirror started...")
