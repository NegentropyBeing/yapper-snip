import pytest

from app import lifecycle
from app.lifecycle import Lifecycle


@pytest.fixture
def exits():
    return []


@pytest.fixture
def make(exits):
    def build(jobs_active=lambda: 0):
        return Lifecycle(exit_fn=lambda code, delay=0: exits.append((code, delay)), jobs_active=jobs_active)

    return build


def test_stop_exits_with_zero_after_a_short_delay(make, exits):
    make().stop()
    assert [code for code, _ in exits] == [0]
    assert exits[0][1] > 0  # leaves time for the response to reach the client


def test_restart_needs_the_launcher(make, exits, monkeypatch):
    monkeypatch.delenv(lifecycle.SUPERVISED_ENV, raising=False)
    with pytest.raises(lifecycle.NotSupervised):
        make().restart()
    assert exits == []

    monkeypatch.setenv(lifecycle.SUPERVISED_ENV, "1")
    make().restart()
    assert [code for code, _ in exits] == [lifecycle.EXIT_RESTART]


def test_restart_code_is_not_the_one_uvicorn_uses_for_a_failed_start():
    assert lifecycle.EXIT_RESTART != 3


def test_exits_only_after_the_last_page_has_been_gone_a_while(make, exits):
    app = make()
    app.tick(1000)
    assert exits == []  # no page has ever opened

    app.page_open("a", now=0)
    app.page_open("b", now=0)
    app.page_closed("a")
    app.tick(1)
    app.tick(lifecycle.PAGE_TIMEOUT + 1)  # b stopped pinging; the grace period starts
    assert exits == []

    app.tick(lifecycle.PAGE_TIMEOUT + 1 + lifecycle.GRACE)
    assert [code for code, _ in exits] == [0]


def test_a_reload_does_not_exit(make, exits):
    app = make()
    app.page_open("a", now=0)
    app.page_closed("a")
    app.tick(1)
    app.page_open("b", now=lifecycle.GRACE - 1)  # the new page arrives within the grace period
    app.tick(lifecycle.GRACE + 1)
    assert exits == []


def test_a_running_job_delays_the_exit(make, exits):
    running = [1]
    app = make(jobs_active=lambda: running[0])
    app.page_open("a", now=0)
    app.page_closed("a")
    app.tick(1)
    app.tick(1 + lifecycle.GRACE)
    assert exits == []

    running[0] = 0
    app.tick(2 + lifecycle.GRACE)
    assert [code for code, _ in exits] == [0]
