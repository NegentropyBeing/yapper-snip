import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Callable, Iterator

# Finished jobs stay readable this long; the UI only polls a job while it runs.
KEEP_FINISHED_SECONDS = 3600


class JobsRunning(RuntimeError):
    pass


class Job:
    def __init__(self, kind: str) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.status = "queued"  # queued | running | done | error
        self.progress = 0.0
        self.message = ""
        self.result: dict = {}
        self.error = ""
        self.finished_at: float | None = None
        self._lock = threading.Lock()

    def update(self, progress: float | None = None, message: str | None = None) -> None:
        with self._lock:
            if progress is not None:
                self.progress = max(0.0, min(1.0, progress))
            if message is not None:
                self.message = message

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "id": self.id, "kind": self.kind, "status": self.status, "progress": self.progress,
                "message": self.message, "result": self.result, "error": self.error,
            }

    def is_finished(self) -> bool:
        with self._lock:
            return self.status in ("done", "error")

    def _start(self) -> None:
        with self._lock:
            self.status = "running"

    def _finish(self, result: dict | None = None, error: str = "") -> None:
        with self._lock:
            self.result = result or {}
            self.error = error
            self.progress = 1.0 if not error else self.progress
            self.status = "error" if error else "done"
            self.finished_at = time.monotonic()


_jobs: dict[str, Job] = {}
_lock = threading.RLock()
_pool = ThreadPoolExecutor(max_workers=2)


def submit(kind: str, fn: Callable[[Job], dict | None]) -> Job:
    job = Job(kind)
    with _lock:
        _evict()
        _jobs[job.id] = job

    def run() -> None:
        job._start()
        try:
            job._finish(fn(job))
        except Exception as exc:  # surfaced to the UI as the job error
            job._finish(error=str(exc) or exc.__class__.__name__)

    _pool.submit(run)
    return job


def _evict() -> None:
    now = time.monotonic()
    for job_id, job in list(_jobs.items()):
        if job.is_finished() and now - (job.finished_at or now) >= KEEP_FINISHED_SECONDS:
            del _jobs[job_id]


def active() -> int:
    with _lock:
        return sum(not job.is_finished() for job in _jobs.values())


@contextmanager
def exclusive() -> Iterator[None]:
    """Run a block while no job is running and none can start; raises JobsRunning otherwise."""
    with _lock:
        if active():
            raise JobsRunning("A job is still running; wait for it or restart the app first")
        yield


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)
