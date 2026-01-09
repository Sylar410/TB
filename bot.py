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

# Get bot token from environment variable (NEVER hardcode it!)
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# Maximum file size in MB (Telegram limit is 50MB for bots)
MAX_FILE_SIZE_MB = 48

# Comprehensive list of supported platforms
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
    'Likee': ['likee.video'],
    'Rumble': ['rumble.com'],
    'Bilibili': ['bilibili.com', 'b23.tv'],
    'Snapchat': ['snapchat.com'],
    'Threads': ['threads.net'],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    platforms_list = '\n'.join([f"• {name}" for name in list(SUPPORTED_PLATFORMS.keys())[:10]])
    
    welcome_message = (
        "👋 Welcome to Universal Video Downloader Bot!\n\n"
        "📹 Supported platforms (30+):\n"
        f"{platforms_list}\n"
        "• And many more!\n\n"
        "💡 Just send me any video link!\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - Get help\n"
        "/platforms - See all platforms\n"
        "/status - Check bot status"
    )
    await update.message.reply_text(welcome_message)

async def platforms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all supported platforms."""
    platforms_text = "🌐 All Supported Platforms:\n\n"
    for platform, domains in SUPPORTED_PLATFORMS.items():
        platforms_text += f"✓ {platform}\n"
    
    platforms_text += "\n💡 If platform not listed, try anyway! Supports 1000+ sites."
    await update.message.reply_text(platforms_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = (
        "🔧 How to use:\n\n"
        "1. Copy any video link\n"
        "2. Send it to me\n"
        "3. Wait for download & upload\n"
        "4. Get your video!\n\n"
        "⚠️ Limitations:\n"
        "• Max file size: 48MB\n"
        "• Private videos won't work\n"
        "• Age-restricted may fail\n"
        "• Some platforms have rate limits\n\n"
        "📝 Supported formats:\n"
        "MP4, WebM, MKV, MOV, and more!\n\n"
        "🆘 If download fails:\n"
        "• Check if video is public\n"
        "• Try copying link again\n"
        "• Make sure link is valid\n"
        "• Wait a moment and retry"
    )
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot status."""
    await update.message.reply_text("✅ Bot is online and ready to download!")

def detect_platform(url):
    """Detect which platform the URL is from."""
    url_lower = url.lower()
    for platform, domains in SUPPORTED_PLATFORMS.items():
        if any(domain in url_lower for domain in domains):
            return platform
    return "Unknown"

def download_video(url):
    """Download video using yt-dlp with aggressive format fallback."""
    os.makedirs('downloads', exist_ok=True)
    
    platform = detect_platform(url)
    logger.info(f"Detected platform: {platform}")
    
    # Multiple format strategies - tries everything possible
    format_strategies = [
        # Strategy 1: Best quality MP4 under size limit
        f'best[ext=mp4][filesize<{MAX_FILE_SIZE_MB}M]',
        
        # Strategy 2: Best quality under size limit (any format)
        f'best[filesize<{MAX_FILE_SIZE_MB}M]',
        
        # Strategy 3: Best video + audio merge (under limit)
        f'bestvideo[filesize<{MAX_FILE_SIZE_MB}M]+bestaudio[filesize<{MAX_FILE_SIZE_MB}M]/best',
        
        # Strategy 4: Worst quality (for large videos)
        'worst[ext=mp4]',
        
        # Strategy 5: Just get anything
        'worst',
        
        # Strategy 6: Best available (no size filter)
        'best',
    ]
    
    for idx, format_string in enumerate(format_strategies):
        logger.info(f"Trying format strategy {idx + 1}: {format_string}")
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_color': True,
            'socket_timeout': 60,
            'retries': 3,
            'fragment_retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            'merge_output_format': 'mp4',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    continue
                
                filename = ydl.prepare_filename(info)
                
                # Try to find the actual downloaded file
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    # Check for various extensions
                    for ext in ['.mp4', '.webm', '.mkv', '.mov', '.avi', '.flv', '.m4v']:
                        test_file = base + ext
                        if os.path.exists(test_file):
                            filename = test_file
                            logger.info(f"Found file: {filename}")
                            break
                
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename) / (1024 * 1024)
                    logger.info(f"Successfully downloaded: {filename} ({file_size:.2f}MB)")
                    
                    # Check if file is too large after download
                    if file_size > 50:
                        logger.warning(f"File too large: {file_size:.2f}MB")
                        os.remove(filename)
                        continue
                    
                    return filename, info.get('title', 'Video'), info.get('duration', 0)
        
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            logger.warning(f"Strategy {idx + 1} failed: {e}")
            
            # Don't retry if it's a clear permanent error
            if any(x in error_msg for x in ['private video', 'not available', 'removed', 'deleted']):
                logger.error("Permanent error detected, stopping retry")
                break
            
            continue
            
        except Exception as e:
            logger.warning(f"Strategy {idx + 1} unexpected error: {e}")
            continue
    
    logger.error(f"All download strategies failed for: {url}")
    return None, None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with URLs."""
    text = update.message.text.strip()
    
    # Basic URL detection
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await update.message.reply_text(
            "❌ No valid URL found!\n\n"
            "Please send a video link from any supported platform.\n"
            "Use /platforms to see all supported sites."
        )
        return
    
    url = urls[0]  # Take first URL
    platform = detect_platform(url)
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"⏳ Downloading from {platform}...\n"
        "Please wait, this may take a moment."
    )
    
    try:
        # Download the video
        filename, title, duration = download_video(url)
        
        if filename and os.path.exists(filename):
            # Get file size
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size > 50:
                await processing_msg.edit_text(
                    f"❌ Video is too large ({file_size:.1f}MB)\n"
                    "Telegram limit: 50MB\n\n"
                    "💡 Try:\n"
                    "• A shorter clip\n"
                    "• Lower quality version"
                )
                os.remove(filename)
                return
            
            # Update status
            await processing_msg.edit_text(
                f"📤 Uploading {file_size:.1f}MB to Telegram...\n"
                "Almost done!"
            )
            
            # Calculate upload timeout based on file size
            upload_timeout = max(120, int(file_size * 10))
            
            # Send the video
            try:
                with open(filename, 'rb') as video:
                    caption = f"🎬 {title[:200]}\n📦 {file_size:.1f}MB | 🌐 {platform}"
                    await update.message.reply_video(
                        video=video,
                        caption=caption,
                        supports_streaming=True,
                        read_timeout=upload_timeout,
                        write_timeout=upload_timeout,
                    )
                
                await processing_msg.delete()
                
            except Exception as upload_error:
                logger.error(f"Upload error: {upload_error}")
                await processing_msg.edit_text(
                    "❌ Failed to upload to Telegram\n\n"
                    "Possible reasons:\n"
                    "• File format not supported\n"
                    "• File corrupted during download\n"
                    "• Network timeout\n\n"
                    "Try again or use a different link"
                )
            
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)
        else:
            error_tips = {
                'Instagram': '• Make sure post/reel is public\n• Try using direct post link',
                'Facebook': '• Video must be public\n• Try share link from video',
                'Twitter/X': '• Use link from share button\n• Check if video is available',
                'Pinterest': '• Use direct pin URL\n• Make sure it\'s a video, not image',
                'TikTok': '• Ensure video is public\n• Account must not be private',
                'YouTube': '• Check if video is available in your region\n• Age-restricted videos may fail',
            }
            
            tip = error_tips.get(platform, '• Verify link is correct\n• Check if content is public')
            
            await processing_msg.edit_text(
                f"❌ Failed to download from {platform}\n\n"
                "Possible reasons:\n"
                "• Video is private/restricted\n"
                "• Link is invalid/expired\n"
                "• Platform blocking downloads\n"
                "• Video too large (>48MB)\n"
                "• Format not supported\n\n"
                f"💡 Tips for {platform}:\n{tip}\n\n"
                "Try another link or platform!"
            )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        try:
            await processing_msg.edit_text(
                "❌ Unexpected error occurred\n\n"
                "Please try:\n"
                "• Sending link again\n"
                "• Waiting a moment\n"
                "• Using different link\n\n"
                "If issue persists, contact bot owner"
            )
        except:
            pass
    
    finally:
        # Cleanup any leftover files
        try:
            for file in os.listdir('downloads'):
                file_path = os.path.join('downloads', file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        return
    
    try:
        # Create the Application
        application = Application.builder().token(BOT_TOKEN).build()

        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("platforms", platforms_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Register error handler
        application.add_error_handler(error_handler)

        # Start the Bot
        logger.info("🚀 Universal Video Downloader Bot Started!")
        logger.info("📡 Listening for video links...")
        logger.info("⚠️  Make sure no other instances are running!")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            pool_timeout=30,
            connect_timeout=30,
            read_timeout=30,
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.error("If you see 'Conflict' error, stop all other bot instances first!")
        raise

if __name__ == '__main__':
    main()
