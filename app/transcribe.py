import importlib.util
import tempfile
from pathlib import Path

from . import audio, models

MODEL_NAME = "turbo"


def available() -> bool:
    return importlib.util.find_spec("whisper") is not None


def run(src: Path, start: float, end: float) -> dict:
    """Draft a transcript of [start, end) seconds of src with Whisper."""
    if not available():
        raise RuntimeError("Transcription is not installed. Run: uv sync --extra ml")

    import whisper

    with models.gpu(), tempfile.TemporaryDirectory() as tmp:
        segment = Path(tmp) / "segment.wav"
        audio.cut(src, segment, start, end, sample_rate=16000, mono=True)
        model = models.load(
            "whisper", lambda: whisper.load_model(MODEL_NAME, download_root=str(models.MODELS_DIR / "whisper"))
        )
        result = model.transcribe(str(segment), fp16=model.device.type == "cuda")
    return {"text": result["text"].strip(), "language": result.get("language")}
