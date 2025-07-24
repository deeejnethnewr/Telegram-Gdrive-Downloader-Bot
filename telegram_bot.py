import os
import re
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import gdown

# Telegram Bot Token එක මෙතන දැමුව යුතුයි
TELEGRAM_BOT_TOKEN = "8371050656:AAHOWlKI_bYINDx78jmBvnt6r19ah32spCY"

# Logger සැකසීම
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Google Drive link එකෙන් file id එක හොයාගන්න regex
GDRIVE_REGEX = r'https?://drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([\w-]+)'

# Download වෙන්න ඇති folder එක
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 හෙලෝ! Google Drive link එකක් එවන්න. මම ඒ file එක download කරලා, local එකට save කරලා ඔබට එවන්නම්."
    )

def download_file(file_id: str):
    url = f'https://drive.google.com/uc?id={file_id}'
    output_path = os.path.join(DOWNLOAD_FOLDER, file_id)
    return gdown.download(url, output_path, quiet=True)

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text or ""
    match = re.search(GDRIVE_REGEX, text)
    if not match:
        update.message.reply_text("❌ හරි Google Drive link එකක් නොමැත. කරුණාකර හරි link එකක් එවන්න.")
        return
    
    file_id = match.group(1)
    update.message.reply_text(f"⏳ Downloading file (ID: {file_id})...")
    
    try:
        file_path = download_file(file_id)
        if not file_path or not os.path.isfile(file_path):
            update.message.reply_text("❌ Download වුනත් file එක සර්වරයේ නොමැත.")
            return
    except Exception as e:
        logger.error(f"Download error: {e}")
        update.message.reply_text("❌ Download කිරීම අසමත් විය. කරුණාකර link එක පරීක්ෂා කරන්න.")
        return
    
    update.message.reply_text(f"✅ Download සාර්ථකයි! File එක මේ තැන save වුනා: {file_path}\nFile එක ඔබට යවමින් පවතී...")
    
    try:
        with open(file_path, 'rb') as f:
            update.message.reply_document(document=f, filename=os.path.basename(file_path))
        update.message.reply_text("📤 File එක සාර්ථකව යවා ඇත!")
    except Exception as e:
        logger.error(f"Send error: {e}")
        update.message.reply_text("❌ File එක යවන්න බැරි විය. ඔබ local folder එකේ ගොනුව ලබා ගත හැක.")

def error_handler(update: object, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)
    
    logger.info("Bot started. Listening for messages...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
