import pytest

from app import clips, isolate, tasks, transcribe
from tests.test_jobs import wait_for


@pytest.fixture
def clip(tmp_path, monkeypatch):
    monkeypatch.setattr(clips, "WORK_DIR", tmp_path / "work")
    with clips.new_clip() as new:
        (new.dir / "original.wav").write_bytes(b"x")
        new.save({"id": new.id, "duration": 10.0})
    return new.id


def test_isolate_writes_the_clean_variant_and_reports_steps(clip, monkeypatch):
    calls = []

    def fake_run(src, dst, steps, on_progress=None):
        calls.append((src.name, dst.name, steps))
        dst.write_bytes(b"clean")
        on_progress(0.5, "halfway")

    monkeypatch.setattr(isolate, "run", fake_run)

    done = wait_for(tasks.start_isolate(clip, ["vocals", "denoise"]))

    assert calls == [("original.wav", "clean.wav", ["vocals", "denoise"])]
    assert done["result"] == {"clip_id": clip, "steps": ["vocals", "denoise"]}
    assert clips.load(clip)["variants"] == ["original", "clean"]


def test_isolate_needs_a_known_step_and_clip(clip):
    with pytest.raises(ValueError):
        tasks.start_isolate(clip, ["nonsense"])
    with pytest.raises(KeyError):
        tasks.start_isolate("ffffffffffff", ["vocals"])


def test_transcribe_returns_the_draft(clip, monkeypatch):
    monkeypatch.setattr(transcribe, "run", lambda src, start, end: {"text": f"{src.name} {start}-{end}", "language": "pt"})

    done = wait_for(tasks.start_transcribe(clip, "original", 1.0, 4.0))

    assert done["result"] == {"text": "original.wav 1.0-4.0", "language": "pt"}


def test_transcribe_rejects_bad_range_and_unknown_variant(clip):
    with pytest.raises(ValueError):
        tasks.start_transcribe(clip, "original", 4.0, 4.0)
    with pytest.raises(KeyError):
        tasks.start_transcribe(clip, "clean", 1.0, 4.0)
