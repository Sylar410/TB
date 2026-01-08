from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import yt_dlp
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

ALLOWED_USERNAME = "Xcvzynavgsh"

async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username

    if user != ALLOWED_USERNAME:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    url = update.message.text.strip()
    await update.message.reply_text("⬇️ Downloading video...")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': 'video.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(filename, 'rb'))
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text("❌ Failed to download video or unsupported link.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, downloader))

print("Bot running...")
app.run_polling()