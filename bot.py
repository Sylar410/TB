import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import yt_dlp
from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= RENDER DUMMY SERVER =================
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Health)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ======================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERNAME = "Xcvzynavgsh"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ydl_opts = {
    "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
    "format": "best",
    "cookiefile": "cookies.txt",
    "quiet": True,
    "noplaylist": True,
    "merge_output_format": "mp4",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ALLOWED_USERNAME:
        await update.message.reply_text("❌ Not authorized")
        return

    keyboard = [["📥 Download Video"]]
    await update.message.reply_text(
        "Send a Facebook or Twitter (X) video link 👇",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyboard)
    )

async def downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_user.username != ALLOWED_USERNAME:
        await update.message.reply_text("❌ Not authorized")
        return

    text = update.message.text.strip()

    if text == "📥 Download Video":
        await update.message.reply_text("🔗 Send the Facebook / Twitter link")
        return

    await update.message.reply_text("⬇️ Downloading...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_video(
            video=open(filename, "rb"),
            supports_streaming=True
        )
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"❌ Failed:\n{str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, downloader))
    app.run_polling()

if __name__ == "__main__":
    main()
