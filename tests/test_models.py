import threading

import pytest

from app import models


@pytest.fixture(autouse=True)
def clean_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(models, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(models, "_loaded", {})


def test_load_calls_loader_once_per_name():
    calls = []

    def loader():
        calls.append(1)
        return object()

    first = models.load("whisper", loader)
    assert models.load("whisper", loader) is first
    assert len(calls) == 1
    assert models.load("other", object) is not first


def test_gpu_admits_one_caller_at_a_time():
    holding = threading.Event()
    release = threading.Event()
    second_in = threading.Event()

    def hold():
        with models.gpu():
            holding.set()
            release.wait(2)

    def contend():
        with models.gpu():
            second_in.set()

    first = threading.Thread(target=hold)
    first.start()
    holding.wait(2)
    second = threading.Thread(target=contend)
    second.start()
    try:
        assert not second_in.wait(0.2)  # blocked while the first holds the GPU
    finally:
        release.set()
        first.join()
        second.join()
    assert second_in.is_set()


def test_purge_drops_loaded_models_and_files(tmp_path):
    models.MODELS_DIR.mkdir()
    (models.MODELS_DIR / "m.ckpt").write_bytes(b"x" * 100)
    loads = []

    def loader():
        loads.append(1)
        return object()

    models.load("whisper", loader)

    assert models.purge() == {"freed_bytes": 100}
    assert list(models.MODELS_DIR.iterdir()) == []
    models.load("whisper", loader)  # fetched again, not served from memory
    assert len(loads) == 2
