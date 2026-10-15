import json
import re
import subprocess
from pathlib import Path

from pydantic import BaseModel

WORK_SAMPLE_RATE = 48000
NORMALIZE_PEAK_DB = -1.0


class AudioError(RuntimeError):
    pass


class CutOptions(BaseModel):
    sample_rate: int | None = None
    mono: bool = False
    fade_ms: float = 0
    normalize: bool = False


def _run(args: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
        raise AudioError(f"{args[0]} failed: {tail}")
    return proc


def parse_timestamp(value: str | float | int | None) -> float | None:
    """Accept seconds ("75", "75.5") or clock times ("1:15", "00:01:15.250")."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = float(value)
    else:
        text = value.strip().replace(",", ".")
        if not text:
            return None
        parts = text.split(":")
        if len(parts) > 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
            raise ValueError(f"Invalid timestamp: {value!r}")
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
    if seconds < 0:
        raise ValueError(f"Invalid timestamp: {value!r}")
    return seconds


def probe(path: Path) -> dict:
    proc = _run([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "format=duration:stream=sample_rate,channels,codec_name",
        "-of", "json", str(path),
    ])
    data = json.loads(proc.stdout)
    stream = data["streams"][0]
    return {
        "duration": float(data["format"]["duration"]),
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "codec": stream["codec_name"],
    }


def to_work_wav(src: Path, dst: Path) -> None:
    _run([
        "ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn",
        "-af", f"aresample={WORK_SAMPLE_RATE}:resampler=soxr",
        "-c:a", "pcm_s16le", str(dst),
    ])


def peak_db(src: Path, start: float, end: float) -> float:
    proc = _run([
        "ffmpeg", "-v", "info", "-nostats", "-i", str(src),
        "-af", f"atrim=start={start:.6f}:end={end:.6f},volumedetect",
        "-f", "null", "-",
    ])
    match = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", proc.stderr)
    if not match or match.group(1) == "-inf":
        raise AudioError("Selection is silent")
    return float(match.group(1))


def cut(
    src: Path,
    dst: Path,
    start: float,
    end: float,
    options: CutOptions | None = None,
) -> None:
    """Cut [start, end) seconds from a PCM file. atrim is sample-accurate."""
    options = options or CutOptions()
    if end <= start:
        raise ValueError("End must be after start")
    duration = end - start
    filters = [f"atrim=start={start:.6f}:end={end:.6f}", "asetpts=PTS-STARTPTS"]
    if options.mono:
        filters.append("aformat=channel_layouts=mono")
    if options.normalize:
        gain = NORMALIZE_PEAK_DB - peak_db(src, start, end)
        filters.append(f"volume={gain:.2f}dB")
    if options.sample_rate:
        filters.append(f"aresample={options.sample_rate}:resampler=soxr")
    fade = min(options.fade_ms / 1000, duration / 2)
    if fade > 0:
        filters.append(f"afade=t=in:st=0:d={fade:.4f}")
        filters.append(f"afade=t=out:st={duration - fade:.6f}:d={fade:.4f}")
    _run([
        "ffmpeg", "-y", "-v", "error", "-i", str(src),
        "-af", ",".join(filters), "-c:a", "pcm_s16le", str(dst),
    ])
