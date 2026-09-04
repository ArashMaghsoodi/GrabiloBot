import logging
import uuid
import html
from typing import List
from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InlineQueryResultAudio,
    InlineQueryResultCachedVideo,
    InlineQueryResultCachedAudio,
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
        media_info = await media_service.get_media_info(resolved_url)
        if not media_info or not media_info.items:
            return

        item = media_info.primary_item
        if not item or not item.formats:
            return

        results = []
        duration_str = format_duration(item.duration) if item.duration else "Media"
        platform_name = item.platform.value.capitalize()

        for idx, fmt in enumerate(item.formats[:10]):
            size_str = human_readable_size(fmt.filesize) if fmt.filesize else "Unknown size"
            cache_key = f"{item.platform.value}:{item.media_id}:{fmt.quality_label}"
            cached_file = cache_service.get_telegram_file(cache_key)

            result_id = f"inline_{item.media_id}_{idx}"
            caption = build_media_caption(item, fmt)

            if cached_file:
                # Fast path: cached file_id instantly sends video/audio directly into the target chat
                file_id = cached_file["file_id"]
                file_type = cached_file["file_type"]

                if file_type == "audio":
                    results.append(
                        InlineQueryResultCachedAudio(
                            id=result_id,
                            audio_file_id=file_id,
                            caption=caption,
                            parse_mode="HTML",
                        )
                    )
                else:
                    results.append(
                        InlineQueryResultCachedVideo(
                            id=result_id,
                            video_file_id=file_id,
                            title=f"{fmt.quality_label} • {size_str}",
                            description=f"{item.title} ({platform_name})",
                            caption=caption,
                            parse_mode="HTML",
                        )
                    )
            else:
                # Uncached path: Send direct text message with status and callback token to trigger background download & send in same chat
                cb_data = f"inlinedl:{item.platform.value}:{item.media_id}:{idx}"
                msg_content = (
                    f"🎬 <b>{html.escape(item.title)}</b>\n"
                    f"<b>Platform:</b> {platform_name} | <b>Quality:</b> {fmt.quality_label} ({size_str})\n\n"
                    "⏳ <i>Downloading media for chat delivery...</i>"
                )
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚡ Processing Download...", callback_data=cb_data)]
                ])

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

    parts = data.split(":")
    if len(parts) != 4:
        return

    _, platform_str, media_id, fmt_idx_str = parts
    fmt_idx = int(fmt_idx_str)

    cached_info = cache_service.get_media_info(f"{platform_str}:{media_id}")
    if not cached_info:
        await query.answer("❌ Media session expired.", show_alert=True)
        return

    from app.services.media_service import media_service
    media_info = media_service._dict_to_media_info(cached_info)
    item = media_info.primary_item

    if not item or fmt_idx >= len(item.formats):
        await query.answer("❌ Selected quality format not found.", show_alert=True)
        return

    selected_format = item.formats[fmt_idx]
    sender = TelegramMediaSender(context.bot)
    cache_key = f"{platform_str}:{media_id}:{selected_format.quality_label}"

    await query.answer(f"Downloading {selected_format.quality_label}...")

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

        caption = build_media_caption(item, selected_format)

        # Target chat identification: inline_message_id if present, else chat_id
        target_kwargs = {}
        if query.inline_message_id:
            target_kwargs["inline_message_id"] = query.inline_message_id
        elif query.message:
            target_kwargs["chat_id"] = query.message.chat_id

        # Since inline messages edited via inline_message_id cannot directly attach new local file binaries via editMessageMedia without existing file_id,
        # we upload media to user context or chat and update/send.
        chat_id = query.message.chat_id if query.message else query.from_user.id
        sent_msg = await sender.send_local_file(
            chat_id=chat_id,
            file_path=file_path,
            is_audio=selected_format.is_audio_only,
            caption=caption,
            parse_mode="HTML",
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

            # Delete the placeholder inline message if in standard chat
            if query.message:
                await query.message.delete()
            elif query.inline_message_id:
                try:
                    await context.bot.edit_message_text(
                        inline_message_id=query.inline_message_id,
                        text="✅ <i>Media delivered below!</i>",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
        else:
            await query.edit_message_text("❌ Failed to deliver media.")

    finally:
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Error cleaning up temp file {file_path}: {e}")
