import threading
import time

import pytest

from app import jobs


def wait_for(job, status="done", timeout=2.0):
    deadline = time.monotonic() + timeout
    while job.to_dict()["status"] not in (status, "error") and time.monotonic() < deadline:
        time.sleep(0.01)
    return job.to_dict()


def test_job_reports_progress_and_result():
    job = jobs.submit("test", lambda job: (job.update(0.5, "halfway"), {"ok": True})[1])

    done = wait_for(job)
    assert done["status"] == "done"
    assert done["progress"] == 1.0
    assert done["result"] == {"ok": True}
    assert jobs.get(job.id) is job


def test_job_failure_is_reported_as_error():
    def boom(job):
        raise ValueError("bad input")

    assert wait_for(jobs.submit("test", boom), "error")["error"] == "bad input"


def test_to_dict_is_a_plain_snapshot():
    job = jobs.submit("test", lambda job: None)
    wait_for(job)
    assert set(job.to_dict()) == {"id", "kind", "status", "progress", "message", "result", "error"}


def test_exclusive_refuses_while_a_job_runs():
    release = threading.Event()
    job = jobs.submit("test", lambda job: release.wait(2) and None)
    try:
        with pytest.raises(jobs.JobsRunning):
            with jobs.exclusive():
                pass
    finally:
        release.set()
        wait_for(job)

    with jobs.exclusive():  # nothing running any more
        pass


def test_submit_waits_for_exclusive_block():
    started = threading.Event()
    with jobs.exclusive():
        thread = threading.Thread(target=lambda: (jobs.submit("test", lambda job: started.set()), None))
        thread.start()
        assert not started.wait(0.2)  # held back while the exclusive block runs
    thread.join()
    assert started.wait(2)


def test_finished_jobs_are_evicted_on_later_submits(monkeypatch):
    first = jobs.submit("test", lambda job: None)
    wait_for(first)
    monkeypatch.setattr(jobs, "KEEP_FINISHED_SECONDS", 0)

    wait_for(jobs.submit("test", lambda job: None))

    assert jobs.get(first.id) is None
