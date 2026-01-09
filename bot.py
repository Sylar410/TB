import os
import re
import logging
import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

# ---------------- PLATFORMS ----------------
SUPPORTED_PLATFORMS = {
    "YouTube": ["youtube.com", "youtu.be"],
    "Instagram": ["instagram.com"],
    "Facebook": ["facebook.com", "fb.watch"],
    "Twitter/X": ["twitter.com", "x.com"],
    "TikTok": ["tiktok.com"],
    "Pinterest": ["pinterest.com", "pin.it"],
    "Reddit": ["reddit.com", "v.redd.it"],
    "Vimeo": ["vimeo.com"],
}

# ---------------- HELPERS ----------------
def detect_platform(url: str) -> str:
    url = url.lower()
    for platform, domains in SUPPORTED_PLATFORMS.items():
        if any(d in url for d in domains):
            return platform
    return "Unknown"


def download_video(url: str):
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": (
            "bv*[ext=mp4]+ba[ext=m4a]/"
            "b[ext=mp4]/"
            "best"
        ),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 60,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for ext in (".mp4", ".webm", ".mkv", ".mov"):
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break

            if not os.path.exists(filename):
                return None, None

            size_mb = os.path.getsize(filename) / (1024 * 1024)
            logger.info(f"Downloaded {filename} ({size_mb:.2f} MB)")

            return filename, info.get("title", "Video")

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None, None


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Universal Video Downloader Bot*\n\n"
        "📥 Send me a video link from:\n"
        "YouTube, Instagram, Facebook, X, TikTok, Pinterest & more.\n\n"
        "⚠️ Private / restricted videos won’t work.",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 *How to use*\n\n"
        "1️⃣ Copy video link\n"
        "2️⃣ Send it here\n"
        "3️⃣ Wait for download\n\n"
        "📌 Works best with public videos.",
        parse_mode="Markdown",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is ONLINE & working")


# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    url_match = re.search(r"https?://\S+", text)
    if not url_match:
        await update.message.reply_text("❌ Please send a valid video link")
        return

    url = url_match.group()
    platform = detect_platform(url)

    msg = await update.message.reply_text(
        f"⏳ Downloading from *{platform}* ...",
        parse_mode="Markdown",
    )

    filename, title = download_video(url)

    if not filename:
        await msg.edit_text(
            "❌ Download failed.\n\n"
            "Possible reasons:\n"
            "• Video is private\n"
            "• Platform blocked download\n"
            "• Invalid link"
        )
        return

    size_mb = os.path.getsize(filename) / (1024 * 1024)
    await msg.edit_text(f"📤 Uploading ({size_mb:.1f} MB)...")

    try:
        with open(filename, "rb") as file:
            await update.message.reply_document(
                document=file,
                caption=f"🎬 {title[:200]}\n🌐 {platform}",
                read_timeout=300,
                write_timeout=300,
            )
        await msg.delete()

    except Exception as e:
        logger.error(f"Upload error: {e}")
        await msg.edit_text("❌ Failed to upload file")

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot started")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
