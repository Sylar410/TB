import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# Maximum file size in MB
MAX_FILE_SIZE_MB = 48

# Supported platforms
SUPPORTED_PLATFORMS = {
    'YouTube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
    'Instagram': ['instagram.com', 'instagr.am'],
    'Facebook': ['facebook.com', 'fb.watch', 'fb.com'],
    'Twitter/X': ['twitter.com', 'x.com', 't.co'],
    'TikTok': ['tiktok.com', 'vm.tiktok.com'],
    'Pinterest': ['pinterest.com', 'pin.it'],
    'Reddit': ['reddit.com', 'v.redd.it'],
    'Vimeo': ['vimeo.com'],
    'Dailymotion': ['dailymotion.com', 'dai.ly'],
    'Twitch': ['twitch.tv', 'clips.twitch.tv'],
    'Streamable': ['streamable.com'],
    'LinkedIn': ['linkedin.com'],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Welcome to Universal Video Downloader Bot!\n\n"
        "📹 Supported platforms:\n"
        "• YouTube\n"
        "• Instagram\n"
        "• Facebook\n"
        "• Twitter/X\n"
        "• TikTok\n"
        "• Pinterest\n"
        "• Reddit\n"
        "• And 20+ more!\n\n"
        "💡 Just send me any video link!\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - Get help\n"
        "/platforms - See all platforms\n"
        "/status - Check bot status"
    )
    await update.message.reply_text(welcome_message)

async def platforms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platforms_text = "🌐 All Supported Platforms:\n\n"
    for platform in SUPPORTED_PLATFORMS.keys():
        platforms_text += f"✓ {platform}\n"
    platforms_text += "\n💡 Try any video link - I support 1000+ sites!"
    await update.message.reply_text(platforms_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔧 How to use:\n\n"
        "1. Copy any video link\n"
        "2. Send it to me\n"
        "3. Wait for download\n"
        "4. Get your video!\n\n"
        "⚠️ Limitations:\n"
        "• Max file size: 48MB\n"
        "• Private videos won't work\n"
        "• Age-restricted may fail\n\n"
        "🆘 If it fails:\n"
        "• Check if video is public\n"
        "• Try link again\n"
        "• Make sure link is valid"
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and ready!")

def detect_platform(url):
    url_lower = url.lower()
    for platform, domains in SUPPORTED_PLATFORMS.items():
        if any(domain in url_lower for domain in domains):
            return platform
    return "Unknown"

def download_video(url):
    os.makedirs('downloads', exist_ok=True)
    platform = detect_platform(url)
    logger.info(f"Detected platform: {platform}")
    
    format_strategies = [
        f'best[ext=mp4][filesize<{MAX_FILE_SIZE_MB}M]',
        f'best[filesize<{MAX_FILE_SIZE_MB}M]',
        f'bestvideo[filesize<{MAX_FILE_SIZE_MB}M]+bestaudio/best',
        'worst[ext=mp4]',
        'worst',
        'best',
    ]
    
    for idx, format_string in enumerate(format_strategies):
        logger.info(f"Trying strategy {idx + 1}: {format_string}")
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'socket_timeout': 60,
            'retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            'merge_output_format': 'mp4',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    continue
                
                filename = ydl.prepare_filename(info)
                
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.webm', '.mkv', '.mov']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            filename = test_file
                            break
                
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename) / (1024 * 1024)
                    logger.info(f"Downloaded: {filename} ({file_size:.2f}MB)")
                    
                    if file_size > 50:
                        os.remove(filename)
                        continue
                    
                    return filename, info.get('title', 'Video'), info.get('duration', 0)
        
        except Exception as e:
            logger.warning(f"Strategy {idx + 1} failed: {e}")
            continue
    
    return None, None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await update.message.reply_text(
            "❌ No valid URL found!\n\n"
            "Send a video link from any supported platform.\n"
            "Use /platforms to see all supported sites."
        )
        return
    
    url = urls[0]
    platform = detect_platform(url)
    
    processing_msg = await update.message.reply_text(
        f"⏳ Downloading from {platform}...\n"
        "Please wait..."
    )
    
    try:
        filename, title, duration = download_video(url)
        
        if filen
