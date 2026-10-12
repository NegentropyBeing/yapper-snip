import importlib.util
import tempfile
import threading
from pathlib import Path
from typing import Callable

from . import audio
from .config import ROOT

MODELS_DIR = ROOT / "models"

# Applied in this order. Each entry: model file, and the output stem to keep.
STEPS = {
    "vocals": ("vocals_mel_band_roformer.ckpt", "vocals"),
    "dereverb": ("dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt", "noreverb"),
    "denoise": ("denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt", "dry"),
}

# One model on the GPU at a time.
gpu_lock = threading.Lock()


def purge_models() -> dict:
    """Delete every downloaded model; they are fetched again on next use."""
    from . import clips

    with gpu_lock:
        return clips.empty_folder(MODELS_DIR)


def available() -> bool:
    return importlib.util.find_spec("audio_separator") is not None


def _pick_stem(outputs: list[str], folder: Path, stem: str) -> Path:
    for name in outputs:
        if f"_({stem})".lower() in Path(name).name.lower():
            path = Path(name)
            return path if path.is_absolute() else folder / path
    raise audio.AudioError(f"Separation produced no '{stem}' stem: {outputs}")


def run(src: Path, dst: Path, steps: list[str], on_progress: Callable[[float, str], None] | None = None) -> None:
    """Run the chosen cleanup steps on src and write the result to dst as a work WAV."""
    chosen = [s for s in STEPS if s in steps]
    if not chosen:
        raise ValueError("Choose at least one cleanup step")
    if not available():
        raise RuntimeError("Voice cleanup is not installed. Run: uv sync --extra ml")

    from audio_separator.separator import Separator

    with gpu_lock, tempfile.TemporaryDirectory(dir=dst.parent) as tmp:
        folder = Path(tmp)
        separator = Separator(output_dir=str(folder), output_format="WAV", model_file_dir=str(MODELS_DIR))
        current = src
        for i, step in enumerate(chosen):
            model, stem = STEPS[step]
            if on_progress:
                on_progress(i / len(chosen), f"Running {step} ({i + 1}/{len(chosen)})")
            separator.load_model(model_filename=model)
            current = _pick_stem(separator.separate(str(current)), folder, stem)
        audio.to_work_wav(current, dst)
