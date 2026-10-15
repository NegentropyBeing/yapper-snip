"""Background jobs that work on a clip. Each start_* validates now, so callers can reject bad input before queueing."""

from . import clips, isolate, jobs, transcribe


def start_isolate(clip_id: str, steps: list[str]) -> jobs.Job:
    src = clips.variant_path(clip_id, "original")
    if not set(steps) & set(isolate.STEPS):
        raise ValueError("Choose at least one cleanup step")
    dst = clips.new_variant_path(clip_id, "clean")

    def work(job: jobs.Job) -> dict:
        isolate.run(src, dst, steps, on_progress=job.update)
        return {"clip_id": clip_id, "steps": steps}

    return jobs.submit("isolate", work)


def start_transcribe(clip_id: str, variant: str, start: float, end: float) -> jobs.Job:
    src = clips.variant_path(clip_id, variant)
    if end <= start:
        raise ValueError("End must be after start")

    def work(job: jobs.Job) -> dict:
        job.update(0.1, "Transcribing")
        return transcribe.run(src, start, end)

    return jobs.submit("transcribe", work)
