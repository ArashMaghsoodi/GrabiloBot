import logging
import shutil
import sys
from pathlib import Path

# Ensure project root is in sys.path when running bot.py directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters,
)

from app.config import config
from app.handlers.start import start_command, help_command, settings_command
from app.handlers.private import handle_private_url, handle_private_callback
from app.handlers.inline import inline_query_handler, inline_callback_handler
from app.handlers.errors import error_handler
from app.services.cache_service import CacheService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def cleanup_temp_dir():
    """Clean up any leftover temporary files on startup"""
    try:
        if config.temp_dir.exists():
            for item in config.temp_dir.iterdir():
                if item.is_file():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
        logger.info("Temporary workspace directory cleaned up.")
    except Exception as e:
        logger.error(f"Error during temp directory startup cleanup: {e}")


def main():
    if not config.bot_token:
        logger.critical("BOT_TOKEN is not set! Please configure .env or environment variable.")
        sys.exit(1)

    cleanup_temp_dir()

    # Expire old database cache
    cache = CacheService()
    cache.cleanup_expired()

    # Build Telegram Bot Application
    builder = Application.builder().token(config.bot_token)
    if config.telegram_api_url:
        custom_url = config.telegram_api_url
        # Ensure the custom URL has a protocol; default to http://
        if not custom_url.startswith(("http://", "https://")):
            custom_url = f"http://{custom_url}"
        # python-telegram-bot expects base_url to end with "/bot"
        if not custom_url.endswith("/bot"):
            custom_url = f"{custom_url.rstrip('/')}/bot"
        builder = builder.base_url(custom_url).base_file_url(custom_url.replace("/bot", "/file/bot"))
        logger.info(f"Using custom local Telegram Bot API server: {config.telegram_api_url}")
    application = builder.build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))

    # Inline Mode Handlers
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CallbackQueryHandler(inline_callback_handler, pattern=r"^inlinedl:"))

    # Private Chat Message & Callback Handlers
    application.add_handler(CallbackQueryHandler(handle_private_callback, pattern=r"^dl:"))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private_url)
    )

    # Error Handler
    application.add_error_handler(error_handler)

    logger.info("GrabiloBot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
