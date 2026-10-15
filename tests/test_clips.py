import json
import shutil

import pytest
from fastapi.testclient import TestClient

from app import clips, config, export, ingest, main
from tests.test_audio import frames, tone  # noqa: F401

CLIP_ID = "0123456789ab"


@pytest.fixture
def client(tmp_path, monkeypatch, tone):  # noqa: F811
    work = tmp_path / "work"
    monkeypatch.setattr(clips, "WORK_DIR", work)
    monkeypatch.setattr(config, "SETTINGS_PATH", tmp_path / "settings.json")
    clip = work / CLIP_ID
    clip.mkdir(parents=True)
    shutil.copy(tone, clip / "original.wav")
    (clip / "meta.json").write_text(json.dumps({"id": CLIP_ID, "duration": 10.0, "created": 1}))
    return TestClient(main.app)


def test_window_pads_and_clamps():
    assert ingest.window(3, 15, 5, 526) == (0.0, 20.0, 3, 15)
    assert ingest.window(520, None, 5, 526) == (515, 526, 520, 526)


@pytest.mark.parametrize("start, end", [(600, 610), (10, 10), (0, 2000)])
def test_window_rejects(start, end):
    with pytest.raises(ValueError):
        ingest.window(start, end, 5, 3600 if end == 2000 else 526)


def test_safe_name():
    assert export.safe_name(' clo:vis/..\\take?.wav ') == "clovis..take"
    with pytest.raises(ValueError):
        export.safe_name("...")


def test_export_requires_output_folder(client):
    body = {"name": "x", "start": 1, "end": 4}
    res = client.post(f"/api/clips/{CLIP_ID}/export", json=body)
    assert res.status_code == 400
    assert "output folder" in res.json()["detail"]


def test_export_writes_wav_and_transcript(client, tmp_path):
    out = tmp_path / "out"
    client.put("/api/settings", json={"output_dir": str(out)})
    body = {"name": "voz", "start": 1.5, "end": 7.5, "sample_rate": 24000, "mono": True, "transcript": "olá"}
    first = client.post(f"/api/clips/{CLIP_ID}/export", json=body).json()
    second = client.post(f"/api/clips/{CLIP_ID}/export", json=body).json()
    assert frames(out / "voz.wav") == (6 * 24000, 24000, 1)
    assert (out / "voz.txt").read_text(encoding="utf-8") == "olá\n"
    assert first["duration"] == pytest.approx(6.0, abs=0.001)
    assert second["path"].endswith("voz-2.wav")


ADMIN = {"X-Yapper": "1"}


def test_admin_routes_need_header(client):
    for action in ("purge-cache", "purge-models", "stop", "restart"):
        assert client.post(f"/api/admin/{action}", json={}).status_code == 403
    assert client.get(f"/api/clips/{CLIP_ID}").status_code == 200


def test_purge_cache_and_purge_models_are_separate(client, tmp_path, monkeypatch, tone):  # noqa: F811
    models = tmp_path / "models"
    (models / "whisper").mkdir(parents=True)
    (models / "whisper" / "m.pt").write_bytes(b"x" * 100)
    monkeypatch.setattr(main.models, "MODELS_DIR", models)

    freed = client.post("/api/admin/purge-cache", headers=ADMIN).json()["freed_bytes"]
    assert freed > 100
    assert client.get("/api/clips").json() == []
    assert (models / "whisper" / "m.pt").exists()

    clip = clips.WORK_DIR / CLIP_ID
    clip.mkdir()
    (clip / "meta.json").write_text(json.dumps({"id": CLIP_ID, "created": 1}))
    assert client.post("/api/admin/purge-models", headers=ADMIN).json() == {"freed_bytes": 100}
    assert list(models.iterdir()) == []
    assert client.get(f"/api/clips/{CLIP_ID}").status_code == 200


def test_purge_refused_while_job_runs(client, monkeypatch):
    monkeypatch.setattr(main.jobs, "active", lambda: 1)
    assert client.post("/api/admin/purge-cache", headers=ADMIN).status_code == 409
    assert client.post("/api/admin/purge-models", headers=ADMIN).status_code == 409
    assert client.get(f"/api/clips/{CLIP_ID}").status_code == 200


def test_stop_and_restart(client, monkeypatch):
    codes = []
    monkeypatch.setattr(main, "_exit_soon", codes.append)
    monkeypatch.delenv("YAPPER_SUPERVISED", raising=False)
    assert client.post("/api/admin/restart", headers=ADMIN).status_code == 409
    monkeypatch.setenv("YAPPER_SUPERVISED", "1")
    assert client.post("/api/admin/restart", headers=ADMIN).status_code == 200
    assert client.post("/api/admin/stop", headers=ADMIN).status_code == 200
    assert codes == [main.EXIT_RESTART, 0]


def test_idle_only_after_last_page_leaves(client, monkeypatch):
    presence = main.presence
    monkeypatch.setattr(presence, "_pages", {})
    monkeypatch.setattr(presence, "_seen", False)
    monkeypatch.setattr(presence, "_empty_since", None)
    assert not presence.idle(1000)  # never opened in a browser

    presence.touch("a", now=0)
    presence.touch("b", now=0)
    assert client.post("/api/presence/a/bye").status_code == 204
    assert not presence.idle(1)
    assert not presence.idle(presence.TIMEOUT + 1)  # b stopped pinging
    assert presence.idle(presence.TIMEOUT + 1 + presence.GRACE)

    assert client.post("/api/presence/c").status_code == 204  # reload
    assert not presence.idle(presence.TIMEOUT + 1 + presence.GRACE)


def test_unknown_clip_and_traversal(client):
    assert client.get("/api/clips/ffffffffffff").status_code == 404
    assert client.get("/api/clips/..%2F..%2Fx/audio").status_code == 404
    assert client.get(f"/api/clips/{CLIP_ID}/audio?variant=clean").status_code == 404
    assert client.get(f"/api/clips/{CLIP_ID}/audio").status_code == 200


def test_capabilities_lists_features(client):
    body = client.get("/api/capabilities").json()
    assert set(body) == {"isolate", "isolate_steps", "transcribe"}
    assert body["isolate_steps"] == ["vocals", "dereverb", "denoise"]
