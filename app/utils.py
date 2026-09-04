import html
from typing import Optional
from app.downloader.models import MediaItem, MediaFormat
from app.downloader.formats import human_readable_size


def format_duration(seconds: Optional[int]) -> str:
    if not seconds or seconds <= 0:
        return "Unknown duration"
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def build_media_caption(item: MediaItem, selected_format: Optional[MediaFormat] = None) -> str:
    lines = [
        f"<b>{html.escape(item.title)}</b>",
        "",
        f"<b>Platform:</b> {item.platform.value.capitalize()}",
    ]
    if item.duration:
        lines.append(f"<b>Duration:</b> {format_duration(item.duration)}")
    if item.author:
        lines.append(f"<b>Author:</b> {html.escape(item.author)}")
    if selected_format:
        size_str = human_readable_size(selected_format.filesize)
        lines.append(f"<b>Quality:</b> {selected_format.quality_label} ({size_str})")

    lines.append("\n<i>Downloaded with @GrabiloBot</i>")
    return "\n".join(lines)
