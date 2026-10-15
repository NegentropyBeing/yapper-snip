import re
from pathlib import Path

from . import audio, clips

_BAD_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


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

    src = clips.variant_path(clip_id, variant)
    meta = clips.load(clip_id)
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
