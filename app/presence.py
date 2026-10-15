"""Tracks the open browser pages."""

import threading
import time


class Presence:
    def __init__(self, timeout: float, grace: float) -> None:
        self.timeout = timeout
        self.grace = grace
        self._pages: dict[str, float] = {}
        self._lock = threading.Lock()
        self._seen = False  # nothing counts as idle until a page has opened at least once
        self._empty_since: float | None = None

    def touch(self, page_id: str, now: float | None = None) -> None:
        with self._lock:
            self._pages[page_id] = time.monotonic() if now is None else now
            self._seen = True

    def leave(self, page_id: str) -> None:
        with self._lock:
            self._pages.pop(page_id, None)

    def refresh(self, now: float) -> None:
        """Count every open page as just seen, e.g. after the machine slept."""
        with self._lock:
            for page_id in self._pages:
                self._pages[page_id] = now

    def idle(self, now: float) -> bool:
        """True once every page that was open has been gone for the grace period."""
        with self._lock:
            for page_id in [p for p, last in self._pages.items() if now - last > self.timeout]:
                del self._pages[page_id]
            if self._pages or not self._seen:
                self._empty_since = None
                return False
            if self._empty_since is None:
                self._empty_since = now
            return now - self._empty_since >= self.grace
