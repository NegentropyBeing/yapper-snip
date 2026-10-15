import json
import re
import shutil
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from . import disk
from .config import WORK_DIR

VARIANTS = ("original", "clean")
_ID_RE = re.compile(r"[0-9a-f]{12}")


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


def new_variant_path(clip_id: str, variant: str) -> Path:
    """Where to write a variant of an existing clip; it shows up in load() once the file exists."""
    if variant not in VARIANTS:
        raise KeyError(variant)
    return clip_dir(clip_id) / f"{variant}.wav"


@dataclass
class NewClip:
    id: str
    dir: Path

    def variant_path(self, variant: str) -> Path:
        if variant not in VARIANTS:
            raise KeyError(variant)
        return self.dir / f"{variant}.wav"

    def save(self, meta: dict) -> None:
        _save(self.dir, meta)


@contextmanager
def new_clip() -> Iterator[NewClip]:
    """Make a clip folder; it is deleted again if the block raises."""
    clip_id = uuid.uuid4().hex[:12]
    path = WORK_DIR / clip_id
    path.mkdir(parents=True)
    try:
        yield NewClip(clip_id, path)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
        raise
