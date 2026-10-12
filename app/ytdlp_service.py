from pathlib import Path
from typing import Callable

import yt_dlp
from yt_dlp.utils import DownloadError, download_range_func

# Some videos carry auto-dubbed tracks next to the original; never pick a dub.
AUDIO_FORMAT = "bestaudio[format_note*=original]/bestaudio/best"

_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "js_runtimes": {"node": {}},
}


class YtdlpError(RuntimeError):
    pass


def _clean(exc: Exception) -> str:
    return str(exc).removeprefix("ERROR: ").strip()


def probe(url: str) -> dict:
    try:
        with yt_dlp.YoutubeDL(_BASE_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as exc:
        raise YtdlpError(_clean(exc)) from exc
    if info.get("is_live"):
        raise YtdlpError("Live streams are not supported")
    if not info.get("duration"):
        raise YtdlpError("Could not determine the video duration")
    return {
        "video_id": info.get("id"),
        "extractor": info.get("extractor_key"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": float(info["duration"]),
        "language": info.get("language"),
        "thumbnail": info.get("thumbnail"),
        "webpage_url": info.get("webpage_url") or url,
        "chapters": [
            {"title": c.get("title"), "start": c.get("start_time"), "end": c.get("end_time")}
            for c in (info.get("chapters") or [])
        ],
    }


def download_range(
    url: str,
    start: float,
    end: float,
    dest_dir: Path,
    on_progress: Callable[[float], None] | None = None,
) -> dict:
    """Download [start, end] seconds of the best original audio track, without re-encoding."""

    def hook(d: dict) -> None:
        if on_progress and d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                on_progress(d.get("downloaded_bytes", 0) / total)

    opts = dict(
        _BASE_OPTS,
        format=AUDIO_FORMAT,
        download_ranges=download_range_func(None, [(start, end)]),
        outtmpl=str(dest_dir / "source.%(ext)s"),
        progress_hooks=[hook],
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except DownloadError as exc:
        raise YtdlpError(_clean(exc)) from exc
    downloads = info.get("requested_downloads") or []
    if not downloads:
        raise YtdlpError("yt-dlp did not produce a file")
    return {
        "path": Path(downloads[0]["filepath"]),
        "format_id": info.get("format_id"),
        "format_note": info.get("format_note"),
        "acodec": info.get("acodec"),
        "abr": info.get("abr"),
    }
