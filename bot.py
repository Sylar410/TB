from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import yt_dlp
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERNAME = "Xcvzynavgsh"

async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != ALLOWED_USERNAME:
        await update.message.reply_text("❌ Not authorized")
        return

    url = update.message.text.strip()

    # Fix YouTube Shorts
    if "youtube.com/shorts/" in url:
        url = url.replace("youtube.com/shorts/", "youtube.com/watch?v=")

    await update.message.reply_text("⬇️ Downloading...")

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": "video.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(file, "rb"))
        os.remove(file)

    except Exception as e:
        await update.message.reply_text("❌ Download failed")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, downloader))

print("Bot running...")
app.run_polling()
