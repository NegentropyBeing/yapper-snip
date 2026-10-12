import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Callable


@dataclass
class Job:
    id: str
    kind: str
    status: str = "queued"  # queued | running | done | error
    progress: float = 0.0
    message: str = ""
    result: dict = field(default_factory=dict)
    error: str = ""

    def update(self, progress: float | None = None, message: str | None = None) -> None:
        if progress is not None:
            self.progress = max(0.0, min(1.0, progress))
        if message is not None:
            self.message = message

    def to_dict(self) -> dict:
        return asdict(self)


_jobs: dict[str, Job] = {}
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=2)


def submit(kind: str, fn: Callable[[Job], dict | None]) -> Job:
    job = Job(id=uuid.uuid4().hex[:12], kind=kind)
    with _lock:
        _jobs[job.id] = job

    def run() -> None:
        job.status = "running"
        try:
            job.result = fn(job) or {}
            job.progress = 1.0
            job.status = "done"
        except Exception as exc:  # surfaced to the UI as the job error
            job.error = str(exc) or exc.__class__.__name__
            job.status = "error"

    _pool.submit(run)
    return job


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)
