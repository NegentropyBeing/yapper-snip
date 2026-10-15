"""When the app exits: on stop, on restart, and once the last page closes.

The launcher (python -m app) restarts the server when it exits with EXIT_RESTART.
"""

import os
import threading
import time
from typing import Callable

from .presence import Presence

# Not 3: uvicorn itself exits with 3 when it cannot start (e.g. the port is taken).
EXIT_RESTART = 75
SUPERVISED_ENV = "YAPPER_SUPERVISED"

# Browsers let a background tab ping as rarely as once a minute.
PAGE_TIMEOUT = 90.0
# Covers a reload, where the old page leaves just before the new one arrives.
GRACE = 10.0
# Leaves time for the response to a stop or restart request to reach the client.
RESPONSE_DELAY = 0.3


class NotSupervised(RuntimeError):
    pass


def os_exit(code: int, delay: float = 0) -> None:
    if delay:
        threading.Timer(delay, os._exit, args=(code,)).start()
    else:
        os._exit(code)


class Lifecycle:
    def __init__(self, exit_fn: Callable[..., None], jobs_active: Callable[[], int]) -> None:
        self._exit = exit_fn
        self._jobs_active = jobs_active
        self._presence = Presence(PAGE_TIMEOUT, GRACE)

    def page_open(self, page_id: str, now: float | None = None) -> None:
        self._presence.touch(page_id, now)

    def page_closed(self, page_id: str) -> None:
        self._presence.leave(page_id)

    def stop(self) -> None:
        self._exit(0, RESPONSE_DELAY)

    def restart(self) -> None:
        if os.environ.get(SUPERVISED_ENV) != "1":
            raise NotSupervised("Restart needs the launcher: start the app with 'uv run python -m app'")
        self._exit(EXIT_RESTART, RESPONSE_DELAY)

    def tick(self, now: float) -> None:
        """Exit once every page is gone and no job is running."""
        if self._presence.idle(now) and not self._jobs_active():
            print("yapper-snip: page closed, stopping", flush=True)
            self._exit(0)

    def watch(self) -> None:
        last = time.monotonic()
        while True:
            time.sleep(1)
            now = time.monotonic()
            if now - last > 5:
                # The machine was asleep; give the open pages time to ping again.
                self._presence.refresh(now)
            last = now
            self.tick(now)
