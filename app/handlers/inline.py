import logging
import uuid
import html
from typing import List
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from app.config import config
from app.downloader.platforms import PlatformResolver
from app.downloader.formats import human_readable_size
from app.services.media_service import media_service
from app.services.cache_service import CacheService
from app.services.queue_service import download_queue
from app.sender.sender import TelegramMediaSender
from app.utils import build_media_caption, format_duration

logger = logging.getLogger(__name__)
cache_service = CacheService()


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    if not query or not query.query.strip():
        return

    user_query = query.query.strip()
    platform, resolved_url = PlatformResolver.identify_platform(user_query)

    if not resolved_url or platform.value == "unknown":
        return

    try:
        # Fast metadata extraction
        media_info = await media_service.get_media_info(resolved_url)
        if not media_info or not media_info.items:
            return

        item = media_info.primary_item
        if not item or not item.formats:
            return

        results = []
        duration_str = format_duration(item.duration) if item.duration else "Media"
        platform_name = item.platform.value.capitalize()

        for idx, fmt in enumerate(item.formats[:10]):  # Limit top 10 qualities
            size_str = human_readable_size(fmt.filesize) if fmt.filesize else "Unknown size"
            
            title = f"🎥 {item.title}" if fmt.has_video else f"🎵 {item.title}"
            description = f"{platform_name} • {duration_str} • {fmt.quality_label} ({size_str})"

            # Short-lived token storing query parameters in context or message content
            cb_data = f"inlinedl:{item.platform.value}:{item.media_id}:{idx}"

            # Message sent when user taps inline result
            msg_content = (
                f"🎬 <b>{html.escape(item.title)}</b>\n"
                f"<b>Platform:</b> {platform_name} | <b>Quality:</b> {fmt.quality_label}\n"
                f"<b>Size:</b> {size_str}\n\n"
                "⏳ <i>Preparing media download...</i>"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬇️ Download Media", callback_data=cb_data)]
            ])

            result_id = f"inline_{item.media_id}_{idx}"
            results.append(
                InlineQueryResultArticle(
                    id=result_id,
                    title=f"{fmt.quality_label} • {size_str}",
                    description=f"{item.title} ({platform_name})",
                    thumbnail_url=item.thumbnail if item.thumbnail else None,
                    input_message_content=InputTextMessageContent(
                        message_text=msg_content,
                        parse_mode="HTML",
                    ),
                    reply_markup=keyboard,
                )
            )

        # Cache inline results for 5 minutes
        await query.answer(results, cache_time=300, is_personal=False)

    except Exception as e:
        logger.error(f"Error handling inline query '{user_query}': {e}", exc_info=True)


async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    if not data.startswith("inlinedl:"):
        return

    await query.answer("Starting media download...")
    parts = data.split(":")
    if len(parts) != 4:
        return

    _, platform_str, media_id, fmt_idx_str = parts
    fmt_idx = int(fmt_idx_str)

    # Re-identify platform and fetch metadata via cache
    # In inline mode we reconstruct or fetch cached info
    # Search cache for url by resolving platform + media_id
    # We can fetch media_info directly if url was cached
    # For inline, we store platform/media_id -> url mapping or fetch via media_service
    # To keep it completely reliable, media_service get_media_info uses cache first
    # So if user pasted URL, it's already in metadata_cache.
    
    # We can edit the inline message to show download progress
    await query.edit_message_text("⏳ <b>Fetching media details...</b>", parse_mode="HTML")

    # Retrieve media_info from cache
    # We reconstruct the probable URL or search cache
    # In our media_service, we can store a key mapping media_id -> media_info
    cached_info = cache_service.get_media_info(f"{platform_str}:{media_id}")
    if not cached_info:
        # Fallback: try search or prompt resend
        await query.edit_message_text("❌ Media session expired. Please re-type the link.")
        return

    from app.services.media_service import media_service
    media_info = media_service._dict_to_media_info(cached_info)
    item = media_info.primary_item

    if not item or fmt_idx >= len(item.formats):
        await query.edit_message_text("❌ Selected quality format not found.")
        return

    selected_format = item.formats[fmt_idx]
    sender = TelegramMediaSender(context.bot)
    cache_key = f"{platform_str}:{media_id}:{selected_format.quality_label}"

    # Check Telegram file cache
    cached_file = cache_service.get_telegram_file(cache_key)
    if cached_file:
        await query.edit_message_text("⚡ Delivering cached media...")
        caption = build_media_caption(item, selected_format)
        # For inline callback, sending file as message in chat
        chat_id = query.message.chat_id if query.message else query.from_user.id
        sent = await sender.send_file_id(
            chat_id=chat_id,
            file_id=cached_file["file_id"],
            file_type=cached_file["file_type"],
            caption=caption,
        )
        if sent and query.message:
            await query.message.delete()
        return

    await query.edit_message_text(
        f"⏳ <b>Downloading {selected_format.quality_label}...</b>", parse_mode="HTML"
    )

    output_prefix = f"grabilo_inline_{uuid.uuid4().hex[:8]}"
    file_path = await download_queue.download_task(
        url=item.url,
        format_id=selected_format.format_id,
        output_prefix=output_prefix,
    )

    if not file_path or not file_path.exists():
        await query.edit_message_text("❌ Download failed. Please try again.")
        return

    try:
        actual_size = file_path.stat().st_size
        if actual_size > config.max_file_size:
            await query.edit_message_text(
                f"❌ File size ({human_readable_size(actual_size)}) exceeds Telegram limits."
            )
            return

        await query.edit_message_text("📤 <b>Sending media...</b>", parse_mode="HTML")
        caption = build_media_caption(item, selected_format)
        chat_id = query.message.chat_id if query.message else query.from_user.id

        sent_msg = await sender.send_local_file(
            chat_id=chat_id,
            file_path=file_path,
            is_audio=selected_format.is_audio_only,
            caption=caption,
            duration=item.duration,
            title=item.title,
            performer=item.author,
        )

        if sent_msg:
            file_type = "audio" if selected_format.is_audio_only else "video"
            telegram_file_id = None
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

            if query.message:
                await query.message.delete()
        else:
            await query.edit_message_text("❌ Failed to deliver media.")

    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Error cleaning up temp file {file_path}: {e}")
