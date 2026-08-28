from pyrogram import Client, filters

@Client.on_message(filters.command("leech"))
async def leech_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /leech <url>")
        return
    
    await message.reply_text("Download started...")
