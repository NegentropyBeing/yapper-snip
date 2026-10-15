import pytest

from app import clips


@pytest.fixture(autouse=True)
def work_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(clips, "WORK_DIR", tmp_path / "work")
    return tmp_path / "work"


def test_new_clip_is_kept_when_the_block_succeeds():
    with clips.new_clip() as clip:
        (clip.dir / "original.wav").write_bytes(b"x")
        clip.save({"id": clip.id, "created": 1})

    loaded = clips.load(clip.id)
    assert loaded["id"] == clip.id
    assert loaded["variants"] == ["original"]


def test_new_clip_is_removed_when_the_block_fails(work_dir):
    with pytest.raises(RuntimeError):
        with clips.new_clip() as clip:
            (clip.dir / "original.wav").write_bytes(b"x")
            raise RuntimeError("download failed")

    assert list(work_dir.iterdir()) == []


def test_new_variant_path_adds_a_variant_to_an_existing_clip():
    with clips.new_clip() as clip:
        clip.save({"id": clip.id})

    path = clips.new_variant_path(clip.id, "clean")
    path.write_bytes(b"x")

    assert clips.variant_path(clip.id, "clean") == path
    assert clips.load(clip.id)["variants"] == ["clean"]


@pytest.mark.parametrize("clip_id, variant", [
    ("ffffffffffff", "clean"),  # no such clip
    ("../../etc", "clean"),
])
def test_new_variant_path_rejects_unknown_clip(clip_id, variant):
    with pytest.raises(KeyError):
        clips.new_variant_path(clip_id, variant)


def test_new_variant_path_rejects_unknown_variant():
    with clips.new_clip() as clip:
        clip.save({"id": clip.id})

    with pytest.raises(KeyError):
        clips.new_variant_path(clip.id, "../meta")
