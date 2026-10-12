import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
WORK_DIR = ROOT / "work"
SETTINGS_PATH = ROOT / "settings.json"

# OmniVoice asks for a 3-10 s reference clip and outputs 24 kHz audio.
DEFAULTS = {
    "output_dir": "",
    "padding": 5.0,
    "sample_rate": 24000,
    "mono": True,
    "fade_ms": 5,
    "normalize": False,
}

# Exit code the server uses to ask the launcher (python -m app) for a restart.
EXIT_RESTART = 3
HOST = "127.0.0.1"
PORT = 8765

# Longest window fetched in one go; the work WAV is decoded in the browser.
MAX_WINDOW_SECONDS = 600


def load_settings() -> dict:
    settings = dict(DEFAULTS)
    if SETTINGS_PATH.exists():
        try:
            stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            stored = {}
        settings.update({k: v for k, v in stored.items() if k in DEFAULTS})
    return settings


def save_settings(changes: dict) -> dict:
    settings = load_settings()
    settings.update({k: v for k, v in changes.items() if k in DEFAULTS})
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings
