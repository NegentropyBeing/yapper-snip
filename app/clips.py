import json
import re
import shutil
import time
import uuid
from pathlib import Path

from . import audio, disk, ytdlp_service
from .config import MAX_WINDOW_SECONDS, WORK_DIR
from .jobs import Job

VARIANTS = ("original", "clean")
_ID_RE = re.compile(r"[0-9a-f]{12}")
_BAD_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def clip_dir(clip_id: str) -> Path:
    if not _ID_RE.fullmatch(clip_id):
        raise KeyError(clip_id)
    path = WORK_DIR / clip_id
    if not (path / "meta.json").exists():
        raise KeyError(clip_id)
    return path


def load(clip_id: str) -> dict:
    path = clip_dir(clip_id)
    meta = json.loads((path / "meta.json").read_text(encoding="utf-8"))
    meta["variants"] = [v for v in VARIANTS if (path / f"{v}.wav").exists()]
    return meta


def _save(path: Path, meta: dict) -> None:
    (path / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def list_all() -> list[dict]:
    if not WORK_DIR.exists():
        return []
    clips = []
    for path in WORK_DIR.iterdir():
        try:
            clips.append(load(path.name))
        except (KeyError, ValueError, OSError):
            continue
    return sorted(clips, key=lambda c: c.get("created", 0), reverse=True)


def delete(clip_id: str) -> None:
    shutil.rmtree(clip_dir(clip_id))


def purge() -> dict:
    """Delete every cached clip."""
    return disk.empty_folder(WORK_DIR)


def variant_path(clip_id: str, variant: str) -> Path:
    if variant not in VARIANTS:
        raise KeyError(variant)
    path = clip_dir(clip_id) / f"{variant}.wav"
    if not path.exists():
        raise KeyError(variant)
    return path


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

    clip_id = uuid.uuid4().hex[:12]
    path = WORK_DIR / clip_id
    path.mkdir(parents=True)
    try:
        job.update(0.1, "Downloading audio")
        download = ytdlp_service.download_range(
            url, win_start, win_end, path,
            on_progress=lambda p: job.update(0.1 + 0.7 * p),
        )
        job.update(0.85, "Converting to WAV")
        source = download.pop("path")
        audio.to_work_wav(source, path / "original.wav")
        work = audio.probe(path / "original.wav")
        meta = {
            "id": clip_id,
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
        }
        _save(path, meta)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
        raise
    return {"clip_id": clip_id}


def safe_name(name: str) -> str:
    name = _BAD_NAME_CHARS.sub("", name).strip().strip(".")
    if name.lower().endswith(".wav"):
        name = name[:-4].strip().strip(".")
    if not name:
        raise ValueError("Invalid file name")
    return name


def _free_path(folder: Path, name: str) -> Path:
    candidate = folder / f"{name}.wav"
    n = 2
    while candidate.exists():
        candidate = folder / f"{name}-{n}.wav"
        n += 1
    return candidate


def export(
    clip_id: str,
    output_dir: str,
    name: str,
    start: float,
    end: float,
    variant: str = "original",
    sample_rate: int | None = None,
    mono: bool = False,
    fade_ms: float = 0,
    normalize: bool = False,
    transcript: str = "",
) -> dict:
    if not output_dir:
        raise ValueError("Choose an output folder first")
    folder = Path(output_dir)
    if not folder.is_absolute():
        raise ValueError("The output folder must be an absolute path")
    folder.mkdir(parents=True, exist_ok=True)

    src = variant_path(clip_id, variant)
    meta = load(clip_id)
    start = max(0.0, start)
    end = min(end, meta["duration"])
    dst = _free_path(folder, safe_name(name))
    audio.cut(src, dst, start, end, sample_rate=sample_rate, mono=mono, fade_ms=fade_ms, normalize=normalize)

    result = {"path": str(dst), **audio.probe(dst)}
    if transcript.strip():
        text_path = dst.with_suffix(".txt")
        text_path.write_text(transcript.strip() + "\n", encoding="utf-8")
        result["transcript_path"] = str(text_path)
    return result
