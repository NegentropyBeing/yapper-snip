"""The machine-learning models: where they live on disk, which is loaded, and one-at-a-time GPU use."""

import threading
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from . import disk
from .config import ROOT

MODELS_DIR = ROOT / "models"

_gpu_lock = threading.Lock()
_loaded: dict[str, Any] = {}


@contextmanager
def gpu() -> Iterator[None]:
    """Hold the GPU: one model runs at a time."""
    with _gpu_lock:
        yield


def load(name: str, loader: Callable[[], Any]) -> Any:
    """Return the model called name, loading it with loader the first time. Call inside gpu()."""
    if name not in _loaded:
        _loaded[name] = loader()
    return _loaded[name]


def purge() -> dict:
    """Unload every model and delete the downloaded files; they are fetched again on next use."""
    with gpu():
        _loaded.clear()
        return disk.empty_folder(MODELS_DIR)
