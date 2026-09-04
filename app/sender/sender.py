import logging
from pathlib import Path
from typing import Optional, Union
from telegram import Bot, Message, InputFile
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramMediaSender:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_file_id(
        self,
        chat_id: Union[int, str],
        file_id: str,
        file_type: str,
        caption: Optional[str] = None,
    ) -> Optional[Message]:
        try:
            if file_type == "audio":
                return await self.bot.send_audio(
                    chat_id=chat_id, audio=file_id, caption=caption
                )
            else:
                return await self.bot.send_video(
                    chat_id=chat_id, video=file_id, caption=caption
                )
        except TelegramError as e:
            logger.error(f"Error sending cached file_id {file_id}: {e}")
            return None

    async def send_local_file(
        self,
        chat_id: Union[int, str],
        file_path: Path,
        is_audio: bool = False,
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        title: Optional[str] = None,
        performer: Optional[str] = None,
    ) -> Optional[Message]:
        if not file_path.exists():
            logger.error(f"File to send does not exist: {file_path}")
            return None

        try:
            with open(file_path, "rb") as f:
                if is_audio:
                    msg = await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=InputFile(f, filename=file_path.name),
                        caption=caption,
                        duration=duration,
                        title=title,
                        performer=performer,
                    )
                else:
                    msg = await self.bot.send_video(
                        chat_id=chat_id,
                        video=InputFile(f, filename=file_path.name),
                        caption=caption,
                        duration=duration,
                        supports_streaming=True,
                    )
                return msg
        except TelegramError as e:
            logger.error(f"Failed to send local file {file_path} to {chat_id}: {e}")
            return None
