from typing import List, Dict, Any, Optional
from app.downloader.models import MediaFormat


def human_readable_size(size_bytes: Optional[int]) -> str:
    if size_bytes is None or size_bytes <= 0:
        return "Unknown size"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {units[i]}"


class FormatNormalizer:
    @staticmethod
    def normalize_yt_dlp_formats(raw_formats: List[Dict[str, Any]], duration: Optional[int] = None) -> List[MediaFormat]:
        normalized: List[MediaFormat] = []
        
        # Categorize formats
        video_formats: Dict[str, Dict[str, Any]] = {}  # quality_height -> best format dict
        audio_formats: List[Dict[str, Any]] = []

        for f in raw_formats:
            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            height = f.get("height")
            filesize = f.get("filesize") or f.get("filesize_approx")
            
            # Estimate filesize if missing and bitrate + duration available
            tbr = f.get("tbr")
            if not filesize and tbr and duration:
                filesize = int((tbr * 1024 * duration) / 8)

            has_v = vcodec is not None and vcodec != "none"
            has_a = acodec is not None and acodec != "none"

            if has_v and height and height > 0:
                quality_key = f"{height}p"
                # Keep the format with better bitrate or audio+video combination
                if quality_key not in video_formats:
                    video_formats[quality_key] = {**f, "_calc_filesize": filesize}
                else:
                    existing = video_formats[quality_key]
                    existing_has_a = existing.get("acodec") is not None and existing.get("acodec") != "none"
                    # Prefer combined audio+video or higher bitrate
                    if (has_a and not existing_has_a) or ((tbr or 0) > (existing.get("tbr") or 0)):
                        video_formats[quality_key] = {**f, "_calc_filesize": filesize}

            elif has_a and not has_v:
                audio_formats.append({**f, "_calc_filesize": filesize})

        # Process height choices into clean order
        target_resolutions = [2160, 1440, 1080, 720, 480, 360, 240, 144]
        for res in target_resolutions:
            key = f"{res}p"
            if key in video_formats:
                fmt = video_formats[key]
                vcodec = fmt.get("vcodec")
                acodec = fmt.get("acodec")
                has_a = acodec is not None and acodec != "none"
                
                format_id = fmt.get("format_id", key)
                # If separate audio/video, indicate bestaudio merge
                if not has_a:
                    format_id = f"{fmt.get('format_id')}+bestaudio/best"

                normalized.append(
                    MediaFormat(
                        format_id=format_id,
                        quality_label=key,
                        extension="mp4",
                        filesize=fmt.get("_calc_filesize"),
                        width=fmt.get("width"),
                        height=fmt.get("height"),
                        has_video=True,
                        has_audio=True,
                        is_audio_only=False,
                        vcodec=vcodec,
                        acodec=acodec,
                        tbr=fmt.get("tbr"),
                    )
                )

        # Process best audio choice
        if audio_formats:
            best_audio = max(audio_formats, key=lambda x: x.get("tbr") or 0)
            abr = int(best_audio.get("abr") or best_audio.get("tbr") or 128)
            ext = best_audio.get("ext", "m4a")
            if ext == "webm":
                ext = "m4a"
            
            normalized.append(
                MediaFormat(
                    format_id=best_audio.get("format_id", "bestaudio"),
                    quality_label=f"Audio ({abr}kbps)",
                    extension=ext,
                    filesize=best_audio.get("_calc_filesize"),
                    has_video=False,
                    has_audio=True,
                    is_audio_only=True,
                    acodec=best_audio.get("acodec"),
                    tbr=best_audio.get("tbr"),
                )
            )

        # Fallback if no specific resolution parsed but formats exist
        if not normalized and raw_formats:
            fmt = raw_formats[-1]
            normalized.append(
                MediaFormat(
                    format_id="best",
                    quality_label="Best Quality",
                    extension=fmt.get("ext", "mp4"),
                    filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
                    has_video=True,
                    has_audio=True,
                )
            )

        return normalized
