import os
import configparser
import logging
from pyrogram import Client, filters
from youtube_dl import YoutubeDL
import gdown

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Config Load ───────────────────────────────────────────────────────────────
config = configparser.ConfigParser()
config.read("config.ini")

API_ID = config.getint("telegram", "api_id")
API_HASH = config.get("telegram", "api_hash")
BOT_TOKEN = config.get("telegram", "bot_token")

DOWNLOAD_FOLDER = config.get("storage", "download_folder", fallback="downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ─── Pyrogram Client Init ─────────────────────────────────────────────────────
bot = Client(
    "downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ─── Utility: Google Drive Download ───────────────────────────────────────────
def download_drive(url, output_dir):
    try:
        filepath = gdown.download(url, output=output_dir, quiet=False)
        return filepath
    except Exception as e:
        logger.error(f"Drive download error: {e}")
        return None

# ─── Utility: Generic downloader via youtube_dl ───────────────────────────────
def download_generic(url, output_dir):
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "format": "best",
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Generic download error: {e}")
        return None

# ─── /download Command Handler ─────────────────────────────────────────────────
@bot.on_message(filters.command("download") & filters.private)
async def cmd_download(client, message):
    if len(message.command) < 2:
        await message.reply_text("▶️ Use: /download <link>")
        return

    url = message.command[1]
    await message.reply_text(f"🔍 Downloading: {url}")

    # Prepare per-user folder
    folder = os.path.join(DOWNLOAD_FOLDER, str(message.from_user.id))
    os.makedirs(folder, exist_ok=True)

    # Choose downloader
    if "drive.google.com" in url:
        filepath = download_drive(url, folder)
    else:
        filepath = download_generic(url, folder)

    if not filepath or not os.path.exists(filepath):
        await message.reply_text("❌ Download failed.")
        return

    # Send file back
    try:
        await message.reply_document(
            document=filepath,
            caption=f"✅ Done: `{os.path.basename(filepath)}`"
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        await message.reply_text("❌ Could not send file.")
    finally:
        try:
            os.remove(filepath)
        except:
            pass

# ─── Bot Start-up ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Bot is up and running...")
    bot.run()

