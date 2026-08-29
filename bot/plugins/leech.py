import os
import time
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import Config

class Leech:
    def __init__(self, client, message):
        self.client = client
        self.message = message
        self.user = message.from_user
        self.link = ""
        self.is_leech = True
        
    async def new_event(self):
        """Main leech event"""
        args = self.message.text.split(" ")
        
        if len(args) < 2:
            await self.message.reply_text(
                "📝 **Usage:** /leech <url> [options]\n\n"
                "**Options:**\n"
                "-doc → As document\n"
                "-med → As media\n"
                "-z → Compress\n"
                "-e → Extract\n\n"
                "**Examples:**\n"
                "/leech https://gofile.io/d/xxx\n"
                "/leech magnet:?xt=urn:btih:xxx\n"
                "/leech https://mega.nz/file/xxx"
            )
            return
            
        self.link = args[1]
        
        # Parse options
        self.as_doc = "-doc" in args
        self.as_med = "-med" in args
        self.compress = "-z" in args
        self.extract = "-e" in args
        
        # Detect link type
        link_type = await self.detect_link_type()
        
        if link_type == 'gofile':
            await self.handle_gofile()
        elif link_type == 'mega':
            await self.handle_mega()
        elif link_type == 'magnet':
            await self.handle_torrent()
        elif link_type == 'direct':
            await self.handle_direct()
        else:
            await self.message.reply_text("❌ Unsupported link!")
            
    async def detect_link_type(self):
        """Detect link type"""
        link = self.link.lower()
        
        if 'gofile.io' in link:
            return 'gofile'
        elif 'mega.nz' in link:
            return 'mega'
        elif link.startswith('magnet:'):
            return 'magnet'
        elif link.startswith('http'):
            return 'direct'
        else:
            return 'unknown'
            
    async def handle_gofile(self):
        """Handle Gofile download"""
        try:
            import requests
            
            # Get Gofile direct link
            server_res = requests.get('https://api.gofile.io/getServer')
            server = server_res.json()['data']['server']
            
            file_id = self.link.split('/')[-1]
            info_res = requests.get(f'https://{server}.gofile.io/getContent?contentId={file_id}')
            data = info_res.json()['data']
            
            for fid, file_info in data['children'].items():
                await self.download_and_upload(file_info)
                break
                
        except Exception as e:
            await self.message.reply_text(f"❌ Gofile error: {str(e)}")
            
    async def handle_mega(self):
        """Handle Mega download"""
        await self.message.reply_text("🔷 Mega download started...")
        # Mega download logic
        
    async def handle_torrent(self):
        """Handle torrent download"""
        await self.message.reply_text("🧲 Torrent download started...")
        # Torrent download logic
        
    async def handle_direct(self):
        """Handle direct download"""
        file_info = {
            'file_name': self.link.split('/')[-1].split('?')[0],
            'file_size': 0,
            'direct_link': self.link
        }
        await self.download_and_upload(file_info)
        
    async def download_and_upload(self, file_info):
        """Download and upload with progress"""
        file_name = file_info['file_name']
        file_size = file_info['file_size']
        direct_link = file_info['direct_link']
        file_path = f"downloads/{file_name}"
        
        os.makedirs("downloads", exist_ok=True)
        
        status_msg = await self.message.reply_text(
            f"📥 **Downloading...**\n\n"
            f"📁 File: `{file_name}`\n"
            f"💾 Size: {file_size / (1024*1024):.1f} MB" if file_size > 0 else
            f"📥 **Downloading...**\n\n📁 File: `{file_name}`",
            parse_mode="markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_leech")]
            ])
        )
        
        try:
            # Download
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_link) as response:
                    if response.status != 200:
                        await status_msg.edit_text("❌ Download failed!")
                        return
                        
                    downloaded = 0
                    start_time = time.time()
                    last_update = 0
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024 * 1024):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            current_time = time.time()
                            if current_time - last_update >= 5 and file_size > 0:
                                last_update = current_time
                                elapsed = current_time - start_time
                                percentage = (downloaded / file_size) * 100
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                eta = (file_size - downloaded) / speed if speed > 0 else 0
                                
                                await status_msg.edit_text(
                                    f"📥 **Downloading...**\n\n"
                                    f"📊 Progress: {percentage:.1f}%\n"
                                    f"💾 Done: {downloaded / (1024*1024):.1f} MB / {file_size / (1024*1024):.1f} MB\n"
                                    f"⚡ Speed: {speed / (1024*1024):.1f} MB/s\n"
                                    f"⏳ ETA: {eta:.0f}s",
                                    parse_mode="markdown"
                                )
                                
            # Upload
            await status_msg.edit_text(
                f"📤 **Uploading...**\n\n📁 File: `{file_name}`",
                parse_mode="markdown"
            )
            
            await self.client.send_document(
                self.message.chat.id,
                file_path,
                caption=f"✅ **Leech Complete!**\n\n"
                       f"📁 File: `{file_name}`\n"
                       f"💾 Size: {os.path.getsize(file_path) / (1024*1024):.1f} MB\n\n"
                       f"**Powered By ZxZone Hub** ❞",
                parse_mode="markdown"
            )
            
            await status_msg.delete()
            os.remove(file_path)
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("leech"))
async def leech_command(client, message):
    """Leech command"""
    bot_loop = asyncio.get_event_loop()
    bot_loop.create_task(Leech(client, message).new_event())
