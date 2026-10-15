import logging
import os
import subprocess
import sys
import threading
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audio, clips, isolate, jobs, models, presence, transcribe, ytdlp_service
from .config import EXIT_RESTART, WEB_DIR, load_settings, save_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The pages ping every few seconds; keep that out of the access log.
    logging.getLogger("uvicorn.access").addFilter(lambda record: "/api/presence/" not in record.getMessage())
    threading.Thread(target=presence.watch, daemon=True).start()
    yield


app = FastAPI(title="yapper-snip", lifespan=lifespan)

_PICK_FOLDER = """
import sys, tkinter, tkinter.filedialog
root = tkinter.Tk()
root.withdraw()
root.attributes("-topmost", True)
print(tkinter.filedialog.askdirectory(parent=root, title=sys.argv[2], initialdir=sys.argv[1] or None))
"""


class ProbeRequest(BaseModel):
    url: str


class ClipRequest(BaseModel):
    url: str
    start: str | float | None = None
    end: str | float | None = None
    padding: float = 5.0


class ExportRequest(BaseModel):
    name: str
    start: float
    end: float
    variant: str = "original"
    sample_rate: int | None = None
    mono: bool = False
    fade_ms: float = 0
    normalize: bool = False
    transcript: str = ""


class IsolateRequest(BaseModel):
    steps: list[str]


class TranscribeRequest(BaseModel):
    start: float
    end: float
    variant: str = "original"


class PickFolderRequest(BaseModel):
    title: str = "Output folder"


class SettingsUpdate(BaseModel):
    output_dir: str | None = None
    padding: float | None = None
    sample_rate: int | None = None
    mono: bool | None = None
    fade_ms: float | None = None
    normalize: bool | None = None


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.post("/api/probe")
def probe(req: ProbeRequest) -> dict:
    try:
        return ytdlp_service.probe(req.url.strip())
    except ytdlp_service.YtdlpError as exc:
        raise _bad_request(exc)


@app.post("/api/clips")
def create_clip(req: ClipRequest) -> dict:
    try:
        start = audio.parse_timestamp(req.start)
        end = audio.parse_timestamp(req.end)
    except ValueError as exc:
        raise _bad_request(exc)
    if not 0 <= req.padding <= 60:
        raise HTTPException(status_code=400, detail="Padding must be between 0 and 60 seconds")
    url = req.url.strip()
    job = jobs.submit("download", lambda job: clips.create(job, url, start, end, req.padding))
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job.to_dict()


@app.get("/api/clips")
def list_clips() -> list[dict]:
    return clips.list_all()


@app.get("/api/clips/{clip_id}")
def get_clip(clip_id: str) -> dict:
    try:
        return clips.load(clip_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip")


@app.delete("/api/clips/{clip_id}")
def delete_clip(clip_id: str) -> dict:
    try:
        clips.delete(clip_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip")
    return {"deleted": clip_id}


@app.get("/api/clips/{clip_id}/audio")
def clip_audio(clip_id: str, variant: str = "original") -> FileResponse:
    try:
        path = clips.variant_path(clip_id, variant)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip or variant")
    return FileResponse(path, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@app.post("/api/clips/{clip_id}/export")
def export_clip(clip_id: str, req: ExportRequest) -> dict:
    try:
        return clips.export(clip_id, load_settings()["output_dir"], **req.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip or variant")
    except (ValueError, OSError, audio.AudioError) as exc:
        raise _bad_request(exc)


@app.get("/api/capabilities")
def capabilities() -> dict:
    return {
        "isolate": isolate.available(),
        "isolate_steps": list(isolate.STEPS),
        "transcribe": transcribe.available(),
    }


@app.post("/api/clips/{clip_id}/isolate")
def isolate_clip(clip_id: str, req: IsolateRequest) -> dict:
    try:
        src = clips.variant_path(clip_id, "original")
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip")
    if not set(req.steps) & set(isolate.STEPS):
        raise HTTPException(status_code=400, detail="Choose at least one cleanup step")

    def work(job: jobs.Job) -> dict:
        isolate.run(src, src.with_name("clean.wav"), req.steps, on_progress=job.update)
        return {"clip_id": clip_id, "steps": req.steps}

    return jobs.submit("isolate", work).to_dict()


@app.post("/api/clips/{clip_id}/transcribe")
def transcribe_clip(clip_id: str, req: TranscribeRequest) -> dict:
    try:
        src = clips.variant_path(clip_id, req.variant)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown clip or variant")
    if req.end <= req.start:
        raise HTTPException(status_code=400, detail="End must be after start")

    def work(job: jobs.Job) -> dict:
        job.update(0.1, "Transcribing")
        return transcribe.run(src, req.start, req.end)

    return jobs.submit("transcribe", work).to_dict()


@app.get("/api/settings")
def get_settings() -> dict:
    return load_settings()


@app.put("/api/settings")
def put_settings(update: SettingsUpdate) -> dict:
    return save_settings(update.model_dump(exclude_none=True))


@app.post("/api/pick-folder")
def pick_folder(req: PickFolderRequest) -> dict:
    # Tk wants the main thread, so the dialog runs in its own process.
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", _PICK_FOLDER, load_settings()["output_dir"], req.title],
        capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail="Could not open the folder dialog")
    path = proc.stdout.strip()
    if not path:
        return {"output_dir": load_settings()["output_dir"], "cancelled": True}
    return {**save_settings({"output_dir": path.replace("/", "\\") if sys.platform == "win32" else path}), "cancelled": False}


@app.post("/api/presence/{page_id}", status_code=204)
def page_open(page_id: str) -> None:
    presence.touch(page_id)


@app.post("/api/presence/{page_id}/bye", status_code=204)
def page_closed(page_id: str) -> None:
    presence.leave(page_id)


def _admin(x_yapper: str | None = Header(default=None)) -> None:
    # A custom header keeps other web pages from triggering these with a plain form post.
    if x_yapper != "1":
        raise HTTPException(status_code=403, detail="Missing X-Yapper header")


def _exit_soon(code: int) -> None:
    # Leave time for the response to reach the client.
    threading.Timer(0.3, os._exit, args=(code,)).start()


def _no_active_jobs() -> None:
    if jobs.active():
        raise HTTPException(status_code=409, detail="A job is still running; wait for it or restart the app first")


@app.post("/api/admin/purge-cache", dependencies=[Depends(_admin), Depends(_no_active_jobs)])
def purge_cache() -> dict:
    return clips.purge()


@app.post("/api/admin/purge-models", dependencies=[Depends(_admin), Depends(_no_active_jobs)])
def purge_models() -> dict:
    return models.purge()


@app.post("/api/admin/stop", dependencies=[Depends(_admin)])
def stop_app() -> dict:
    _exit_soon(0)
    return {"stopping": True}


@app.post("/api/admin/restart", dependencies=[Depends(_admin)])
def restart_app() -> dict:
    if os.environ.get("YAPPER_SUPERVISED") != "1":
        raise HTTPException(status_code=409, detail="Restart needs the launcher: start the app with 'uv run python -m app'")
    _exit_soon(EXIT_RESTART)
    return {"restarting": True}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
