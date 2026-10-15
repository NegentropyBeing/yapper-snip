import shutil
from pathlib import Path


def _tree_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def empty_folder(folder: Path) -> dict:
    freed = 0
    if folder.exists():
        for entry in folder.iterdir():
            if entry.is_dir():
                freed += _tree_size(entry)
                shutil.rmtree(entry, ignore_errors=True)
            else:
                freed += entry.stat().st_size
                entry.unlink(missing_ok=True)
    return {"freed_bytes": freed}
