import time

from . import audio, clips, ytdlp_service
from .config import MAX_WINDOW_SECONDS
from .jobs import Job


def window(start: float | None, end: float | None, padding: float, duration: float) -> tuple[float, float, float, float]:
    """Return (window_start, window_end, sel_start, sel_end) in video time."""
    sel_start = 0.0 if start is None else start
    sel_end = duration if end is None else min(end, duration)
    if sel_start >= duration:
        raise ValueError("Start is past the end of the video")
    if sel_end <= sel_start:
        raise ValueError("End must be after start")
    win_start = max(0.0, sel_start - padding)
    win_end = min(duration, sel_end + padding)
    if win_end - win_start > MAX_WINDOW_SECONDS:
        raise ValueError(f"Range is too long: at most {MAX_WINDOW_SECONDS // 60} minutes including padding")
    return win_start, win_end, sel_start, sel_end


def create(job: Job, url: str, start: float | None, end: float | None, padding: float) -> dict:
    job.update(0.02, "Reading video info")
    info = ytdlp_service.probe(url)
    win_start, win_end, sel_start, sel_end = window(start, end, padding, info["duration"])

    with clips.new_clip() as clip:
        job.update(0.1, "Downloading audio")
        download = ytdlp_service.download_range(
            url, win_start, win_end, clip.dir,
            on_progress=lambda p: job.update(0.1 + 0.7 * p),
        )
        job.update(0.85, "Converting to WAV")
        source = download.pop("path")
        original = clip.variant_path("original")
        audio.to_work_wav(source, original)
        work = audio.probe(original)
        clip.save({
            "id": clip.id,
            "url": info["webpage_url"],
            "video_id": info["video_id"],
            "title": info["title"],
            "uploader": info["uploader"],
            "window_start": win_start,
            "window_end": win_end,
            # Rough selection, relative to the start of the work WAV.
            "sel_start": sel_start - win_start,
            "sel_end": min(sel_end - win_start, work["duration"]),
            "duration": work["duration"],
            "source": {"file": source.name, **download},
            "created": time.time(),
        })
    return {"clip_id": clip.id}
