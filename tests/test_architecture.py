"""Rules about where things may live, checked by reading the source."""

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"


def sources():
    return {path.name: path.read_text(encoding="utf-8") for path in APP.glob("*.py")}


def files_matching(pattern: str, ignore: set[str]) -> list[str]:
    return sorted(name for name, text in sources().items() if name not in ignore and re.search(pattern, text))


def test_only_lifecycle_exits_the_process():
    assert files_matching(r"os\._exit|sys\.exit", ignore={"lifecycle.py", "__main__.py"}) == []


def test_only_the_clip_store_knows_variant_file_names():
    assert files_matching(r"(original|clean)\.wav", ignore={"clips.py"}) == []


def test_only_models_owns_the_models_folder_and_gpu_lock():
    assert files_matching(r"MODELS_DIR\s*=|Lock\(\)", ignore={"models.py", "jobs.py", "presence.py"}) == []
