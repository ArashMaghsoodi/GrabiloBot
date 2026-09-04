import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable
from app.config import config
from app.downloader.engine import MediaDownloaderEngine

logger = logging.getLogger(__name__)


class DownloadQueueService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(config.max_concurrent_downloads)
        self.engine = MediaDownloaderEngine()

    async def download_task(
        self,
        url: str,
        format_id: str,
        output_prefix: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Optional[Path]:
        logger.info(f"Queuing download for {url} ({format_id})")
        async with self.semaphore:
            logger.info(f"Starting download for {url} ({format_id})")
            try:
                # Enforce download timeout
                return await asyncio.wait_for(
                    self.engine.download_format(
                        url=url,
                        format_id=format_id,
                        output_prefix=output_prefix,
                        progress_callback=progress_callback,
                    ),
                    timeout=config.download_timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"Download timed out after {config.download_timeout}s for {url}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in download task: {e}", exc_info=True)
                return None


download_queue = DownloadQueueService()
