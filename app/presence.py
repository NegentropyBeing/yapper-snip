"""Tracks the open browser pages so the server can exit once the last one closes."""

import os
import threading
import time

from . import jobs

# Browsers let a background tab ping as rarely as once a minute.
TIMEOUT = 90.0
# Covers a reload, where the old page leaves just before the new one arrives.
GRACE = 10.0

_pages: dict[str, float] = {}
_lock = threading.Lock()
_seen = False  # nothing exits until a page has opened at least once
_empty_since: float | None = None


def touch(page_id: str, now: float | None = None) -> None:
    global _seen
    with _lock:
        _pages[page_id] = time.monotonic() if now is None else now
        _seen = True


def leave(page_id: str) -> None:
    with _lock:
        _pages.pop(page_id, None)


def idle(now: float) -> bool:
    """True once every page that was open has been gone for GRACE seconds."""
    global _empty_since
    with _lock:
        for page_id in [p for p, last in _pages.items() if now - last > TIMEOUT]:
            del _pages[page_id]
        if _pages or not _seen:
            _empty_since = None
            return False
        if _empty_since is None:
            _empty_since = now
        return now - _empty_since >= GRACE


def watch() -> None:
    last = time.monotonic()
    while True:
        time.sleep(1)
        now = time.monotonic()
        if now - last > 5:
            # The machine was asleep; give the open pages time to ping again.
            with _lock:
                for page_id in _pages:
                    _pages[page_id] = now
        last = now
        if idle(now) and not jobs.active():
            print("yapper-snip: page closed, stopping", flush=True)
            os._exit(0)
