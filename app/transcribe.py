import importlib.util
import tempfile
from pathlib import Path

from . import audio
from .isolate import MODELS_DIR, gpu_lock

MODEL_NAME = "turbo"

_model = None


def available() -> bool:
    return importlib.util.find_spec("whisper") is not None


def run(src: Path, start: float, end: float) -> dict:
    """Draft a transcript of [start, end) seconds of src with Whisper."""
    if not available():
        raise RuntimeError("Transcription is not installed. Run: uv sync --extra ml")

    import whisper

    global _model
    with gpu_lock, tempfile.TemporaryDirectory() as tmp:
        segment = Path(tmp) / "segment.wav"
        audio.cut(src, segment, start, end, sample_rate=16000, mono=True)
        if _model is None:
            _model = whisper.load_model(MODEL_NAME, download_root=str(MODELS_DIR / "whisper"))
        result = _model.transcribe(str(segment), fp16=_model.device.type == "cuda")
    return {"text": result["text"].strip(), "language": result.get("language")}
