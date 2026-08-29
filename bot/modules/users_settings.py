from asyncio import sleep
from ast import literal_eval
from pyrogram.enums import ButtonStyle
from functools import partial
from html import escape
from io import BytesIO
from os import getcwd
from re import sub
from time import time

from aiofiles.os import makedirs, remove
from aiofiles.os import path as aiopath
from langcodes import Language
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler


from .. import auth_chats, excluded_extensions, sudo_users, user_data
from ..core.config_manager import Config
from ..core.seedr_client import SeedrClient
from ..core.tg_client import TgClient
from ..helper.ext_utils.bot_utils import (
    get_size_bytes,
    new_task,
    update_user_ldata,
)
from ..helper.ext_utils.db_handler import database
from ..helper.ext_utils.mega_utils import get_mega_account_info
from ..helper.ext_utils.media_utils import create_thumb
from ..helper.ext_utils.status_utils import get_readable_file_size
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_file,
    send_message,
)

handler_dict = {}

leech_options = [
    "THUMBNAIL",
    "LEECH_SPLIT_SIZE",
    "LEECH_DUMP_CHAT",
    "LEECH_PREFIX",
    "LEECH_SUFFIX",
    "LEECH_CAPTION",
    "THUMBNAIL_LAYOUT",
]
uphoster_options = [
    "GOFILE_TOKEN",
    "GOFILE_FOLDER_ID",
    "BUZZHEAVIER_TOKEN",
    "BUZZHEAVIER_FOLDER_ID",
    "PIXELDRAIN_KEY",
    "DEVUPLOADS_KEY",
    "DEVUPLOADS_FOLDER",
    "VIKINGFILE_HASH",
    "VIKINGFILE_FOLDER",
]
rclone_options = ["RCLONE_CONFIG", "RCLONE_PATH", "RCLONE_FLAGS"]
gdrive_options = ["TOKEN_PICKLE", "GDRIVE_ID", "INDEX_URL", "DRIVE_CAT"]
ffset_options = [
    "FFMPEG_CMDS",
    "METADATA",
    "AUDIO_METADATA",
    "VIDEO_METADATA",
    "SUBTITLE_METADATA",
]
advanced_options = [
    "EXCLUDED_EXTENSIONS",
    "NAME_SWAP",
    "YT_DLP_OPTIONS",
    "UPLOAD_PATHS",
    "USER_COOKIE_FILE",
]
yt_options = ["YT_DESP", "YT_TAGS", "YT_CATEGORY_ID", "YT_PRIVACY_STATUS"]
mega_options = ["MEGA_EMAIL", "MEGA_PASSWORD"]
seedr_options = ["SEEDR_EMAIL", "SEEDR_PASSWORD", "SEEDR_DELETE_FOLDER"]

user_settings_text = {
    "THUMBNAIL": (
        "Photo or Doc",
        "Custom Thumbnail is used as the thumbnail for the files you upload to telegram in media or document mode.",
        "<i>Send a photo to save it as custom thumbnail.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_CONFIG": (
        "",
        "",
        "<i>Send your <code>rclone.conf</code> file to use as your Upload Dest to RClone.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "TOKEN_PICKLE": (
        "",
        "",
        "<i>Send your <code>token.pickle</code> to use as your Upload Dest to GDrive</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_SPLIT_SIZE": (
        "",
        "",
        f"Send Leech split size in bytes or use gb or mb. Example: 40000000 or 2.5gb or 1000mb. PREMIUM_USER: {TgClient.IS_PREMIUM_USER}.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_DUMP_CHAT": (
        "",
        "",
        """Send leech destination ID/USERNAME/PM. 
* b:id/@username/pm (b: means leech by bot) (id or username of the chat or write pm means private message so bot will send the files in private to you) when you should use b:(leech by bot)? When your default settings is leech by user and you want to leech by bot for specific task.
* u:id/@username(u: means leech by user) This in case OWNER added USER_STRING_SESSION.
* h:id/@username(hybrid leech) h: to upload files by bot and user based on file size.
* id/@username|topic_id(leech in specific chat and topic) add | without space and write topic id after chat id or username.
┖ <b>Time Left :</b> <code>60 sec</code>""",
    ),
    "LEECH_PREFIX": (
        "",
        "",
        "Send Leech Filename Prefix. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_SUFFIX": (
        "",
        "",
        "Send Leech Filename Suffix. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "LEECH_CAPTION": (
        "",
        "",
        "Send Leech Caption. You can add HTML tags. Example: <code>@mychannel</code>.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "THUMBNAIL_LAYOUT": (
        "",
        "",
        "Send thumbnail layout (widthxheight, 2x2, 3x3, 2x4, 4x4, ...). Example: 3x3.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_PATH": (
        "",
        "",
        "Send Rclone Path. If you want to use your rclone config edit using owner/user config from usetting or add mrcc: before rclone path. Example mrcc:remote:folder. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "RCLONE_FLAGS": (
        "",
        "",
        "key:value|key|key|key:value . Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>\nEx: --buffer-size:8M|--drive-starred-only",
    ),
    "GDRIVE_ID": (
        "",
        "",
        "Send Gdrive ID. If you want to use your token.pickle edit using owner/user token from usetting or add mtp: before the id. Example: mtp:F435RGGRDXXXXXX . </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "INDEX_URL": (
        "",
        "",
        "Send Index URL for your gdrive option. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "UPLOAD_PATHS": (
        "",
        "",
        "Send Dict of keys that have path values. Example: {'path 1': 'remote:rclonefolder', 'path 2': 'gdrive1 id', 'path 3': 'tg chat id', 'path 4': 'mrcc:remote:', 'path 5': b:@username} . </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "EXCLUDED_EXTENSIONS": (
        "",
        "",
        "Send excluded extensions separated by space without dot at beginning. </i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "NAME_SWAP": (
        "",
        "",
        """<i>Send your Name Swap. You can add pattern instead of normal text according to the format.</i>
<b>Full Documentation Guide</b> <a href="https://t.me/WZML_X/77">Click Here</a>
┖ <b>Time Left :</b> <code>60 sec</code>
""",
    ),
    "YT_DLP_OPTIONS": (
        "",
        "",
        """Format: {key: value, key: value, key: value}.
Example: {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.

<i>Send dict of YT-DLP Options according to format.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>""",
    ),
    "FFMPEG_CMDS": (
        "",
        "",
        """Dict of list values of ffmpeg commands. You can set multiple ffmpeg commands for all files before upload. Don't write ffmpeg at beginning, start directly with the arguments.
Examples: {"subtitle": ["-i mltb.mkv -c copy -c:s srt mltb.mkv", "-i mltb.video -c copy -c:s srt mltb"], "convert": ["-i mltb.m4a -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb.audio -c:a libmp3lame -q:a 2 mltb.mp3"], extract: ["-i mltb -map 0:a -c copy mltb.mka -map 0:s -c copy mltb.srt"]}
Notes:
- Add `-del` to the list which you want from the bot to delete the original files after command run complete!
- To execute one of those lists in bot for example, you must use -ff subtitle (list key) or -ff convert (list key)
Here I will explain how to use mltb.* which is reference to files you want to work on.
1. First cmd: the input is mltb.mkv so this cmd will work only on mkv videos and the output is mltb.mkv also so all outputs are mkv. -del will delete the original media after complete run of the cmd.
2. Second cmd: the input is mltb.video so this cmd will work on all videos and the output is only mltb so the extension is the same as input files.
3. Third cmd: the input is mltb.m4a so this cmd will work only on m4a audios and the output is mltb.mp3 so the output extension is mp3.
4. Fourth cmd: the input is mltb.audio so this cmd will work on all audios and the output is mltb.mp3 so the output extension is mp3.

<i>Send dict of FFMPEG_CMDS Options according to format.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>
""",
    ),
    "METADATA": (
        "🏷 Global Metadata (key=value|key=value)",
        "Apply metadata to all media files with dynamic variables.",
        """<i>📝 Send metadata as</i> <code>key=value|key2=value2</code>

<b>🔧 Dynamic Variables:</b>
• <code>{filename}</code> - Original filename
• <code>{basename}</code> - Name without extension
• <code>{audiolang}</code> - Audio language (English/Hindi etc.)
• <code>{year}</code> - Year from filename

<b>📋 Example:</b>
<code>title={basename}|artist={audiolang} Version|year={year}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "AUDIO_METADATA": (
        "🎵 Audio Stream Metadata",
        "Metadata applied to each audio track separately.",
        """<i>🎧 Audio stream metadata with per-track language support</i>

<b>📋 Example:</b>
<code>language={audiolang}|title=Audio - {audiolang}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "VIDEO_METADATA": (
        "🎥 Video Stream Metadata",
        "Metadata applied to video streams.",
        """<i>📹 Video stream metadata for visual tracks</i>

<b>📋 Example:</b>
<code>title={basename}|comment=HD Video</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "SUBTITLE_METADATA": (
        "💬 Subtitle Stream Metadata",
        "Metadata applied to each subtitle track separately.",
        """<i>📄 Subtitle stream metadata with per-track language support</i>

<b>📋 Example:</b>
<code>language={sublang}|title=Subtitles - {sublang}</code>

⏱ <b>Time Left:</b> <code>60 sec</code>""",
    ),
    "YT_DESP": (
        "String",
        "Custom description for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube description.</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_TAGS": (
        "Comma-separated strings",
        "Custom tags for YouTube uploads (e.g., tag1,tag2,tag3). Default is used if not set.",
        "<i>Send your custom YouTube tags as a comma-separated list.</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_CATEGORY_ID": (
        "Number",
        "Custom category ID for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube category ID (e.g., 22).</i> \nTime Left : <code>60 sec</code>",
    ),
    "YT_PRIVACY_STATUS": (
        "public, private, or unlisted",
        "Custom privacy status for YouTube uploads. Default is used if not set.",
        "<i>Send your custom YouTube privacy status (public, private, or unlisted).</i> \nTime Left : <code>60 sec</code>",
    ),
    "USER_COOKIE_FILE": (
        "File",
        "User's YT-DLP Cookie File to authenticate access to websites and youtube.",
        "<i>Send your cookie file (e.g., cookies.txt or abc.txt).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "GOFILE_TOKEN": (
        "String",
        "Gofile API Token",
        "<i>Send your Gofile API Token.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "GOFILE_FOLDER_ID": (
        "String",
        "Gofile Folder ID",
        "<i>Send your Gofile Folder ID. If empty, uploads to Root.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "BUZZHEAVIER_TOKEN": (
        "String",
        "BuzzHeavier API Token",
        "<i>Send your BuzzHeavier API Token (Account ID).</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "BUZZHEAVIER_FOLDER_ID": (
        "String",
        "BuzzHeavier Folder ID",
        "<i>Send your BuzzHeavier Folder ID.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "PIXELDRAIN_KEY": (
        "String",
        "PixelDrain API Key",
        "<i>Send your PixelDrain API Key.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "DEVUPLOADS_KEY": (
        "String",
        "DevUploads API Key",
        "<i>Send your DevUploads API Key.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "DEVUPLOADS_FOLDER": (
        "String",
        "DevUploads Folder ID",
        "<i>Send your DevUploads Folder ID. Leave empty to upload to root.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIKINGFILE_HASH": (
        "String",
        "VikingFile Hash",
        "<i>Send your VikingFile User Hash.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "VIKINGFILE_FOLDER": (
        "String",
        "VikingFile folder name/path. Leave empty to upload to root.",
        "<i>Send your VikingFile folder name/path. Leave empty to upload to root.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "MEGA_EMAIL": (
        "String",
        "Your Mega.nz account email for per-user Mega downloads & uploads.",
        "<i>Send your Mega.nz email address.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "MEGA_PASSWORD": (
        "String",
        "Your Mega.nz account password for per-user Mega downloads & uploads.",
        "<i>Send your Mega.nz account password.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SEEDR_EMAIL": (
        "String",
        "Your Seedr.cc account email for per-user Seedr cloud downloads.",
        "<i>Send your Seedr.cc email address.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "SEEDR_PASSWORD": (
        "String",
        "Your Seedr.cc account password for per-user Seedr cloud downloads.",
        "<i>Send your Seedr.cc account password.</i> \n┖ <b>Time Left :</b> <code>60 sec</code>",
    ),
    "DRIVE_CAT": (
        "Dict",
        'User-defined GDrive categories (name → drive_id). Format: {"name": "drive_id|index_link"}.',
        '<i>Send dict of user drive categories.\nExample: {"Movies": "0Bxxxxxxxx", "TV": "1Ayyyyyyy|https://index.tv"}\nEach value: drive_id or drive_id|index_link</i> \n┖ <b>Time Left :</b> <code>60 sec</code>',
    ),
}


async def get_user_settings(from_user, stype="main"):
    user_id = from_user.id
    user_name = from_user.mention(style="html")
    buttons = ButtonMaker()
    rclone_conf = f"rclone/{user_id}.conf"
    token_pickle = f"tokens/{user_id}.pickle"
    user_dict = user_data.get(user_id, {})

    if stype == "main":
        buttons.data_button(
            "General Settings", f"userset {user_id} general", position="header"
        )
        buttons.data_button("Mirror Settings", f"userset {user_id} mirror")
        buttons.data_button("Leech Settings", f"userset {user_id} leech")
        buttons.data_button("Uphoster Settings", f"userset {user_id} uphoster")
        buttons.data_button("FF Media Settings", f"userset {user_id} ffset")
        buttons.data_button(
            "Misc Settings", f"userset {user_id} advanced", position="l_body"
        )

        if user_dict and any(
            key in user_dict
            for key in list(user_settings_text.keys())
            + [
                "USER_TOKENS",
                "AS_DOCUMENT",
                "AUTO_THUMBNAIL",
                "EQUAL_SPLITS",
                "MEDIA_GROUP",
                "STOP_DUPLICATE",
                "DEFAULT_UPLOAD",
            ]
        ):
            buttons.data_button(
                "Reset All", f"userset {user_id} confirm_reset_all", position="footer"
            )
        buttons.data_button(
            "Close",
            f"userset {user_id} close",
            position="footer",
            style=ButtonStyle.DANGER,
        )

        text = f"""⌬ <b>User Settings :</b>
│
┟ <b>Name</b> → {user_name}
┠ <b>UserID</b> → #ID{user_id}
┠ <b>Username</b> → @{from_user.username}
┠ <b>Telegram DC</b> → {from_user.dc_id}
┖ <b>Telegram Lang</b> → {Language.get(lc).display_name() if (lc := from_user.language_code) else "N/A"}"""

        btns = buttons.build_menu(2)

    elif stype == "general":
        if user_dict.get("DEFAULT_UPLOAD", ""):
            default_upload = user_dict["DEFAULT_UPLOAD"]
        elif "DEFAULT_UPLOAD" not in user_dict:
            default_upload = Config.DEFAULT_UPLOAD
        du = "GDRIVE API" if default_upload == "gd" else "RCLONE"
        dur = "GDRIVE API" if default_upload != "gd" else "RCLONE"
        buttons.data_button(
            f"Swap to {dur} Mode", f"userset {user_id} {default_upload}"
        )

        user_tokens = user_dict.get("USER_TOKENS", False)
        tr = "USER" if user_tokens else "OWNER"
        trr = "OWNER" if user_tokens else "USER"
        buttons.data_button(
            f"Swap to {trr} token/config",
            f"userset {user_id} tog USER_TOKENS {'f' if user_tokens else 't'}",
        )

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )

        def_cookies = user_dict.get("USE_DEFAULT_COOKIE", False)
        cookie_mode = "Owner's Cookie" if def_cookies else "User's Cookie"
        buttons.data_button(
            f"Swap to {'OWNER' if not def_cookies else 'USER'}'s Cookie File",
            f"userset {user_id} tog USE_DEFAULT_COOKIE {'f' if def_cookies else 't'}",
        )
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>General Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>Default Upload Package</b> → <b>{du}</b>
┠ <b>Default Usage Mode</b> → <b>{tr}'s</b> token/config
┖ <b>YT Cookies Mode</b> → <b>{cookie_mode}</b>
"""

    elif stype == "leech":
        thumbpath = f"thumbnails/{user_id}.jpg"
        buttons.data_button("Thumbnail", f"userset {user_id} menu THUMBNAIL")
        thumbmsg = "Exists" if await aiopath.exists(thumbpath) else "Not Exists"
        buttons.data_button(
            "Leech Split Size", f"userset {user_id} menu LEECH_SPLIT_SIZE"
        )
        if user_dict.get("LEECH_SPLIT_SIZE", False):
            split_size = user_dict["LEECH_SPLIT_SIZE"]
        else:
            split_size = Config.LEECH_SPLIT_SIZE
        buttons.data_button(
            "Leech Destination", f"userset {user_id} menu LEECH_DUMP_CHAT"
        )
        if user_dict.get("LEECH_DUMP_CHAT", False):
            leech_dest = user_dict["LEECH_DUMP_CHAT"]
        elif "LEECH_DUMP_CHAT" not in user_dict and Config.LEECH_LOG_CHAT:
            leech_dest = Config.LEECH_LOG_CHAT
        else:
            leech_dest = "None"
        buttons.data_button("Leech Prefix", f"userset {user_id} menu LEECH_PREFIX")
        if user_dict.get("LEECH_PREFIX", False):
            lprefix = user_dict["LEECH_PREFIX"]
        elif "LEECH_PREFIX" not in user_dict and Config.LEECH_PREFIX:
            lprefix = Config.LEECH_PREFIX
        else:
            lprefix = "Not Exists"
        buttons.data_button("Leech Suffix", f"userset {user_id} menu LEECH_SUFFIX")
        if user_dict.get("LEECH_SUFFIX", False):
            lsuffix = user_dict["LEECH_SUFFIX"]
        elif "LEECH_SUFFIX" not in user_dict and Config.LEECH_SUFFIX:
            lsuffix = Config.LEECH_SUFFIX
        else:
            lsuffix = "Not Exists"

        buttons.data_button("Leech Caption", f"userset {user_id} menu LEECH_CAPTION")
        if user_dict.get("LEECH_CAPTION", False):
            lcap = user_dict["LEECH_CAPTION"]
        elif "LEECH_CAPTION" not in user_dict and Config.LEECH_CAPTION:
            lcap = Config.LEECH_CAPTION
        else:
            lcap = "Not Exists"

        if (
            user_dict.get("AS_DOCUMENT", False)
            or "AS_DOCUMENT" not in user_dict
            and Config.AS_DOCUMENT
        ):
            ltype = "DOCUMENT"
            buttons.data_button("Send As Media", f"userset {user_id} tog AS_DOCUMENT f")
        else:
            ltype = "MEDIA"
            buttons.data_button(
                "Send As Document", f"userset {user_id} tog AS_DOCUMENT t"
            )
        if (
            user_dict.get("EQUAL_SPLITS", False)
            or "EQUAL_SPLITS" not in user_dict
            and Config.EQUAL_SPLITS
        ):
            buttons.data_button(
                "Disable Equal Splits", f"userset {user_id} tog EQUAL_SPLITS f"
            )
            equal_splits = "Enabled"
        else:
            buttons.data_button(
                "Enable Equal Splits", f"userset {user_id} tog EQUAL_SPLITS t"
            )
            equal_splits = "Disabled"
        if (
            user_dict.get("MEDIA_GROUP", False)
            or "MEDIA_GROUP" not in user_dict
            and Config.MEDIA_GROUP
        ):
            buttons.data_button(
                "Disable Media Group", f"userset {user_id} tog MEDIA_GROUP f"
            )
            media_group = "Enabled"
        else:
            buttons.data_button(
                "Enable Media Group", f"userset {user_id} tog MEDIA_GROUP t"
            )
            media_group = "Disabled"
        if (
            user_dict.get("AUTO_THUMBNAIL", False)
            or "AUTO_THUMBNAIL" not in user_dict
            and Config.AUTO_THUMBNAIL
        ):
            buttons.data_button(
                "Disable Auto Thumbnail", f"userset {user_id} tog AUTO_THUMBNAIL f"
            )
            auto_thumb = "Enabled"
        else:
            buttons.data_button(
                "Enable Auto Thumbnail", f"userset {user_id} tog AUTO_THUMBNAIL t"
            )
            auto_thumb = "Disabled"
        buttons.data_button(
            "Thumbnail Layout", f"userset {user_id} menu THUMBNAIL_LAYOUT"
        )
        if user_dict.get("THUMBNAIL_LAYOUT", False):
            thumb_layout = user_dict["THUMBNAIL_LAYOUT"]
        elif "THUMBNAIL_LAYOUT" not in user_dict and Config.THUMBNAIL_LAYOUT:
            thumb_layout = Config.THUMBNAIL_LAYOUT
        else:
            thumb_layout = "None"

        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )
        btns = buttons.build_menu(2)

        text = f"""⌬ <b>Leech Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ Leech Type → <b>{ltype}</b>
┠ Leech Thumbnail → <b>{thumbmsg}</b>
┠ Leech Split Size → <b>{get_readable_file_size(split_size)}</b>
┠ Equal Splits → <b>{equal_splits}</b>
┠ Media Group → <b>{media_group}</b>
┠ Leech Prefix → <code>{escape(lprefix)}</code>
┠ Leech Suffix → <code>{escape(lsuffix)}</code>
┠ Leech Caption → <code>{escape(lcap)}</code>
┠ Leech Destination → <code>{leech_dest}</code>
┠ Thumbnail Layout → <b>{thumb_layout}</b>
┖ Auto Thumbnail → <b>{auto_thumb}</b>
"""

    elif stype == "uphoster":
        uphoster_service = user_dict.get("UPHOSTER_SERVICE", "gofile")
        buttons.data_button(
            "Change Destination ⇋", f"userset {user_id} uphoster_destinations", "header"
        )
        buttons.data_button("Gofile Tools", f"userset {user_id} gofile")
        buttons.data_button("BuzzHeavier Tools", f"userset {user_id} buzzheavier")
        buttons.data_button("PixelDrain Tools", f"userset {user_id} pixeldrain")
        buttons.data_button("DevUploads Tools", f"userset {user_id} devuploads")
        buttons.data_button("VikingFile Tools", f"userset {user_id} vikingfile")
        buttons.data_button("Back", f"userset {user_id} back", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )
        btns = buttons.build_menu(2)

        destinations = [s.capitalize() for s in uphoster_service.split(",")]
        text = f"""⌬ <b>Uphoster Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┖ <b>Current Destination</b> → {", ".join(destinations)}"""

    elif stype == "pixeldrain":
        buttons.data_button("PixelDrain Key", f"userset {user_id} menu PIXELDRAIN_KEY")
        buttons.data_button("Back", f"userset {user_id} back uphoster", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )
        btns = buttons.build_menu(1)

        if user_dict.get("PIXELDRAIN_KEY", False):
            pdtoken = user_dict["PIXELDRAIN_KEY"]
        elif Config.PIXELDRAIN_KEY:
            pdtoken = Config.PIXELDRAIN_KEY
        else:
            pdtoken = "None"

        text = f"""⌬ <b>PixelDrain Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┖ <b>PixelDrain Key</b> → <code>{pdtoken}</code>"""

    elif stype == "buzzheavier":
        buttons.data_button(
            "BuzzHeavier Token", f"userset {user_id} menu BUZZHEAVIER_TOKEN"
        )
        buttons.data_button(
            "BuzzHeavier Folder ID", f"userset {user_id} menu BUZZHEAVIER_FOLDER_ID"
        )
        buttons.data_button("Back", f"userset {user_id} back uphoster", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )
        btns = buttons.build_menu(1)

        if user_dict.get("BUZZHEAVIER_TOKEN", False):
            bztoken = user_dict["BUZZHEAVIER_TOKEN"]
        elif Config.BUZZHEAVIER_API:
            bztoken = Config.BUZZHEAVIER_API
        else:
            bztoken = "None"

        if user_dict.get("BUZZHEAVIER_FOLDER_ID", False):
            bzfolder = user_dict["BUZZHEAVIER_FOLDER_ID"]
        else:
            bzfolder = "None"

        text = f"""⌬ <b>BuzzHeavier Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>BuzzHeavier Token</b> → <code>{bztoken}</code>
┖ <b>BuzzHeavier Folder ID</b> → <code>{bzfolder}</code>"""

    elif stype == "devuploads":
        buttons.data_button(
            "DevUploads API Key", f"userset {user_id} menu DEVUPLOADS_KEY"
        )
        buttons.data_button(
            "DevUploads Folder ID", f"userset {user_id} menu DEVUPLOADS_FOLDER"
        )
        buttons.data_button("Back", f"userset {user_id} back uphoster", "footer")
        buttons.data_button(
            "Close", f"userset {user_id} close", "footer", style=ButtonStyle.DANGER
        )
        btns = buttons.build_menu(1)

        dukey = user_dict.get("DEVUPLOADS_KEY") or Config.DEVUPLOADS_KEY or "None"
        dufolder = (
            user_dict.get("DEVUPLOADS_FOLDER")
            or Config.DEVUPLOADS_FOLDER
            or "None (Root)"
        )
        text = f"""⌬ <b>DevUploads Settings :</b>
┟ <b>Name</b> → {user_name}
┃
┠ <b>DevUploads Key</b> → <code>{dukey}</code>
┖ <b>DevUploads Folder ID</b> → <code>{dufolder}</code>"""

    elif stype == "vikingfile":
        buttons.data_button(
            "VikingFile Hash", f"userset {user_id} menu VIKINGFILE_HASH"
        )
        buttons.data_button(
            "VikingFile Folder", f"userset {user_id} menu VIKINGFILE_FOLDER"
        )
        buttons.data
