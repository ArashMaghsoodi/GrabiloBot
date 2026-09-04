import time
import asyncio
import logging
import uuid
import html
from typing import List
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.config import config
from app.downloader.platforms import PlatformResolver
from app.downloader.models import MediaInfo, MediaItem, MediaFormat
from app.downloader.formats import human_readable_size
from app.services.media_service import media_service
from app.services.cache_service import CacheService
from app.services.queue_service import download_queue
from app.sender.sender import TelegramMediaSender
from app.utils import build_media_caption, format_duration

logger = logging.getLogger(__name__)
cache_service = CacheService()


def build_private_keyboard(media_info: MediaInfo) -> InlineKeyboardMarkup:
    primary_item = media_info.primary_item
    if not primary_item or not primary_item.formats:
        return InlineKeyboardMarkup([])

    buttons: List[List[InlineKeyboardButton]] = []
    video_row: List[InlineKeyboardButton] = []
    audio_buttons: List[InlineKeyboardButton] = []

    for idx, fmt in enumerate(primary_item.formats):
        size_str = human_readable_size(fmt.filesize) if fmt.filesize else ""
        label = f"{fmt.quality_label}" + (f" ({size_str})" if size_str else "")
        cb_data = f"dl:{primary_item.platform.value}:{primary_item.media_id}:{idx}"

        if fmt.is_audio_only:
            audio_buttons.append(InlineKeyboardButton(f"🎵 {label}", callback_data=cb_data))
        else:
            video_row.append(InlineKeyboardButton(f"🎬 {label}", callback_data=cb_data))
            if len(video_row) == 2:
                buttons.append(video_row)
                video_row = []

    if video_row:
        buttons.append(video_row)

    for ab in audio_buttons:
        buttons.append([ab])

    return InlineKeyboardMarkup(buttons)


async def handle_private_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    if not cache_service.check_rate_limit(user_id):
        await update.message.reply_text("⚠️ You are sending requests too quickly. Please wait a moment.")
        return

    text = update.message.text.strip()
    platform, resolved_url = PlatformResolver.identify_platform(text)

    if not resolved_url or platform.value == "unknown":
        await update.message.reply_text("❌ Unsupported URL. Please send a valid YouTube, TikTok, or Instagram link.")
        return

    status_msg = await update.message.reply_text("🔍 Analyzing media link, please wait...")

    try:
        media_info = await media_service.get_media_info(resolved_url)
        if not media_info or not media_info.items:
            await status_msg.edit_text("❌ Could not retrieve media information. The content may be private or unavailable.")
            return

        item = media_info.primary_item
        if not item:
            await status_msg.edit_text("❌ No downloadable media found.")
            return

        if item.duration and item.duration > config.max_duration:
            await status_msg.edit_text(
                f"❌ Media duration ({format_duration(item.duration)}) exceeds maximum limit of {format_duration(config.max_duration)}."
            )
            return

        context.user_data[f"media:{item.platform.value}:{item.media_id}"] = media_info

        desc_lines = [
            f"🎬 <b>{html.escape(item.title)}</b>\n",
            f"<b>Platform:</b> {item.platform.value.capitalize()}",
        ]
        if item.author:
            desc_lines.append(f"<b>Author:</b> {html.escape(item.author)}")
        if item.duration:
            desc_lines.append(f"<b>Duration:</b> {format_duration(item.duration)}")

        desc_lines.append("\n<b>Choose quality to download:</b>")
        keyboard = build_private_keyboard(media_info)

        await status_msg.edit_text("\n".join(desc_lines), parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error analyzing URL in private mode: {e}", exc_info=True)
        await status_msg.edit_text("❌ An error occurred while analyzing the link. Please try again.")


async def handle_private_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    data = query.data

    if not data.startswith("dl:"):
        return

    parts = data.split(":")
    if len(parts) != 4:
        return

    _, platform_str, media_id, fmt_idx_str = parts
    fmt_idx = int(fmt_idx_str)

    media_info: MediaInfo = context.user_data.get(f"media:{platform_str}:{media_id}")
    if not media_info:
        await query.edit_message_text("⚠️ This session has expired. Please send the link again.")
        return

    item = media_info.primary_item
    if not item or fmt_idx >= len(item.formats):
        await query.edit_message_text("❌ Invalid format selected.")
        return

    selected_format: MediaFormat = item.formats[fmt_idx]

    if selected_format.filesize and selected_format.filesize > config.max_file_size:
        await query.edit_message_text(
            f"⚠️ The selected quality ({selected_format.quality_label} - {human_readable_size(selected_format.filesize)}) "
            f"exceeds the maximum upload limit of {human_readable_size(config.max_file_size)}.\n"
            "Please choose a lower resolution."
        )
        return

    sender = TelegramMediaSender(context.bot)
    cache_key = f"{platform_str}:{media_id}:{selected_format.quality_label}"

    cached_file = cache_service.get_telegram_file(cache_key)
    if cached_file:
        await query.edit_message_text("⚡ Reusing cached Telegram media...")
        caption = build_media_caption(item, selected_format)
        sent = await sender.send_file_id(
            chat_id=query.message.chat_id,
            file_id=cached_file["file_id"],
            file_type=cached_file["file_type"],
            caption=caption,
            parse_mode="HTML",
        )
        if sent:
            await query.message.delete()
            return

    await query.edit_message_text(f"⏳ Downloading <b>{selected_format.quality_label}</b>: 0%", parse_mode="HTML")

    loop = asyncio.get_running_loop()
    last_update_time = [0.0]

    def on_progress(percent: float, downloaded_bytes: int, total_bytes: int, speed: float, eta: int):
        now = time.time()
        # Rate limit Telegram UI message edits (once per ~1.5s to avoid flood control)
        if now - last_update_time[0] >= 1.5 or percent >= 100.0:
            last_update_time[0] = now
            pct_str = f"{percent:.1f}%"
            speed_str = human_readable_size(int(speed)) + "/s" if speed else ""
            extra_info = f" ({speed_str})" if speed_str else ""
            text = f"⏳ Downloading <b>{selected_format.quality_label}</b>: {pct_str}{extra_info}"
            asyncio.run_coroutine_threadsafe(
                query.edit_message_text(text, parse_mode="HTML"), loop
            )

    output_prefix = f"grabilo_{uuid.uuid4().hex[:8]}"
    file_path = await download_queue.download_task(
        url=item.url,
        format_id=selected_format.format_id,
        output_prefix=output_prefix,
        progress_callback=on_progress,
    )

    if not file_path or not file_path.exists():
        await query.edit_message_text("❌ Download failed or timed out. Please try again.")
        return

    try:
        actual_size = file_path.stat().st_size
        if actual_size > config.max_file_size:
            await query.edit_message_text(
                f"❌ Downloaded file ({human_readable_size(actual_size)}) is too large to send on Telegram."
            )
            return

        await query.edit_message_text("📤 Uploading media to Telegram...")
        caption = build_media_caption(item, selected_format)
        
        sent_msg = await sender.send_local_file(
            chat_id=query.message.chat_id,
            file_path=file_path,
            is_audio=selected_format.is_audio_only,
            caption=caption,
            parse_mode="HTML",
            duration=item.duration,
            title=item.title,
            performer=item.author,
        )

        if sent_msg:
            telegram_file_id = None
            file_type = "audio" if selected_format.is_audio_only else "video"
            if sent_msg.video:
                telegram_file_id = sent_msg.video.file_id
            elif sent_msg.audio:
                telegram_file_id = sent_msg.audio.file_id
            elif sent_msg.document:
                telegram_file_id = sent_msg.document.file_id

            if telegram_file_id:
                cache_service.set_telegram_file(
                    cache_key=cache_key,
                    file_id=telegram_file_id,
                    file_type=file_type,
                    caption=caption,
                )

            await query.message.delete()
        else:
            await query.edit_message_text("❌ Failed to send file to Telegram.")

    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Error cleaning up temp file {file_path}: {e}")
