import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 <b>Welcome to GrabiloBot!</b>\n"
        "Your open-source Telegram downloader for YouTube, TikTok, and Instagram.\n\n"
        "<b>Two Ways to Use GrabiloBot:</b>\n\n"
        "1️⃣ <b>Private Chat — Download Center</b>\n"
        "Send any supported link directly here for maximum control:\n"
        "• Choose video resolution (2160p to 1440p to 144p)\n"
        "• Extract audio only\n"
        "• Inspect file sizes before downloading\n\n"
        "2️⃣ <b>Inline Mode — Quick Share</b>\n"
        "Type <code>@GrabiloBot &lt;link&gt;</code> in any chat or group to instantly share media with friends without entering private chat!\n\n"
        "<b>Supported Platforms:</b>\n"
        "• YouTube (Videos, Shorts)\n"
        "• TikTok (Videos)\n"
        "• Instagram (Reels, Posts, IGTV)\n\n"
        "Try sending a link now!"
    )
    if update.message:
        await update.message.reply_html(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ <b>GrabiloBot Help & Guide</b>\n\n"
        "• <b>Private Mode:</b> Just paste a link here. The bot will analyze it and display quality options.\n"
        "• <b>Inline Mode:</b> In any chat, type <code>@GrabiloBot https://youtu.be/...</code> and pick a quality button.\n\n"
        "<b>Commands:</b>\n"
        "/start - Welcome message & features\n"
        "/help - Usage instructions\n"
        "/settings - Bot settings & defaults\n"
    )
    if update.message:
        await update.message.reply_html(help_text)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings_text = (
        "⚙️ <b>GrabiloBot Settings</b>\n\n"
        "• <b>Default Quality:</b> Best Available\n"
        "• <b>Default Container:</b> MP4\n"
        "• <b>File Size Limit:</b> Configured by admin\n\n"
        "<i>Settings customization will be expanded in future releases.</i>"
    )
    if update.message:
        await update.message.reply_html(settings_text)
