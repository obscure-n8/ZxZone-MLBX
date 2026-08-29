import os
import time
import asyncio
import aiohttp
import aiofiles
import psutil
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_progress_bar(percentage):
    """10 block progress bar"""
    blocks = int(percentage / 10)
    return f"[{'●' * blocks}{'o' * (10 - blocks)}]"

def format_size(size):
    """Format size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def format_speed(speed):
    """Format speed"""
    return f"{format_size(speed)}/s"

def format_eta(seconds):
    """Format ETA"""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    else:
        return f"{seconds//3600}h {(seconds%3600)//60}m"

def get_system_stats():
    """Get system stats"""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    free = psutil.disk_usage('/').free
    return cpu, ram, format_size(free)

async def get_gofile_info(url):
    """Get Gofile file info"""
    try:
        server_res = requests.get('https://api.gofile.io/getServer')
        server = server_res.json()['data']['server']
        
        file_id = url.split('/')[-1]
        info_res = requests.get(f'https://{server}.gofile.io/getContent?contentId={file_id}')
        data = info_res.json()['data']
        
        for fid, file_info in data['children'].items():
            return {
                'direct_link': file_info['link'],
                'file_name': file_info['name'],
                'file_size': file_info['size']
            }
    except:
        pass
    return None

async def create_status_view(task_id, file_name, total_size, done, start_time, user_name, status="Downloading"):
    """Create status view"""
    percentage = (done / total_size) * 100 if total_size > 0 else 0
    elapsed = time.time() - start_time
    speed = done / elapsed if elapsed > 0 else 0
    eta = (total_size - done) / speed if speed > 0 else 0
    
    cpu, ram, free = get_system_stats()
    bar = get_progress_bar(percentage)
    
    text = f"""
**ZxZone-MLBX Bot**
┌ **ZxZone-HK-MLB**
└ `/leech1 {task_id}`

▍ **Powered By ZxZone Hub** ❞

1. `{file_name}`
┌ **Task By {user_name}**
│ {bar} {percentage:.1f}%
│ **Status** : {status}
│ **Total** : {format_size(total_size)} | **Done** : {format_size(done)}
│ **Speed** : {format_speed(speed)} | **ETA** : {format_eta(eta)}
│ **Engine** : Gofile | **Mode** : `#Leech`
> **Stop** : `/c_{task_id}`

⬢ **BOT STATS**
┌ **CPU** : {cpu}% | **RAM** : {ram}%
└ **FREE** : {free}
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("♻️ Refresh", callback_data=f"refresh_{task_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}")
        ]
    ])
    
    return text, keyboard

@Client.on_message(filters.command("leech"))
async def leech_command(client, message):
    """Leech command with status view"""
    user = message.from_user
    
    if len(message.command) < 2:
        await message.reply_text(
            "📝 **Usage:** /leech <url>\n\n"
            "**Example:**\n"
            "/leech https://gofile.io/d/xxxxx"
        )
        return
    
    url = message.command[1]
    task_id = str(int(time.time()))[-8:]
    
    # Gofile
    if 'gofile.io' in url:
        await message.reply_text("🔍 **Fetching Gofile info...**")
        
        file_info = await get_gofile_info(url)
        
        if not file_info:
            await message.reply_text("❌ Invalid Gofile link!")
            return
            
        file_name = file_info['file_name']
        file_size = file_info['file_size']
        direct_link = file_info['direct_link']
    else:
        file_name = url.split('/')[-1].split('?')[0] or f"file_{task_id}"
        file_size = 0
        direct_link = url
    
    file_path = f"downloads/{task_id}_{file_name}"
    os.makedirs("downloads", exist_ok=True)
    
    # Create initial status view
    status_text, keyboard = await create_status_view(
        task_id, file_name, file_size, 0, time.time(), user.first_name, "Starting"
    )
    
    status_msg = await message.reply_text(status_text, reply_markup=keyboard, parse_mode="markdown")
    
    try:
        # Download
        async with aiohttp.ClientSession() as session:
            async with session.get(direct_link) as response:
                if response.status != 200:
                    await status_msg.edit_text("❌ Download failed!")
                    return
                    
                if file_size == 0:
                    file_size = int(response.headers.get('content-length', 0))
                    
                downloaded = 0
                start_time = time.time()
                last_update = 0
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        if current_time - last_update >= 3:
                            last_update = current_time
                            
                            status_text, keyboard = await create_status_view(
                                task_id, file_name, file_size, downloaded,
                                start_time, user.first_name, "Downloading"
                            )
                            
                            try:
                                await status_msg.edit_text(status_text, reply_markup=keyboard, parse_mode="markdown")
                            except:
                                pass
                                
        # Upload status
        status_text, keyboard = await create_status_view(
            task_id, file_name, file_size, file_size,
            start_time, user.first_name, "Uploading"
        )
        await status_msg.edit_text(status_text, reply_markup=keyboard, parse_mode="markdown")
        
        # Upload
        final_size = os.path.getsize(file_path)
        
        if final_size > 2 * 1024 * 1024 * 1024:
            await status_msg.edit_text("❌ File too large (Max 2GB)!")
            os.remove(file_path)
            return
            
        await client.send_document(
            message.chat.id,
            file_path,
            caption=f"✅ **Leech Complete!**\n\n"
                   f"📁 File: `{file_name}`\n"
                   f"💾 Size: {format_size(final_size)}\n\n"
                   f"**Powered By ZxZone Hub** ❞",
            parse_mode="markdown"
        )
        
        # Complete status
        await status_msg.edit_text(
            f"""
**ZxZone-MLBX Bot**
┌ **ZxZone-HK-MLB**
└ `/leech1 {task_id}`

▍ **Powered By ZxZone Hub** ❞

1. `{file_name}`
┌ **Task By {user.first_name}**
│ [●●●●●●●●●●] 100.0%
│ **Status** : Completed
│ **Total** : {format_size(final_size)} | **Done** : {format_size(final_size)}
│ **Engine** : Gofile | **Mode** : `#Leech`

✅ **Task Completed Successfully!**
""",
            parse_mode="markdown"
        )
        
        os.remove(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
