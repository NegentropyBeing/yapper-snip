# yapper-snip

Cut a short, clean, single-speaker voice snippet from a YouTube video, ready to use as a reference clip for OmniVoice voice cloning.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` and `ffprobe` on the PATH
- Node.js on the PATH (yt-dlp uses it to read YouTube pages)
- Optional: an NVIDIA GPU for voice cleanup and transcript drafts

## Run

```
uv sync                # downloader, trim editor and export only
uv sync --extra ml     # also voice cleanup and transcript drafts (several GB)
uv run uvicorn app.main:app --port 8765
```

Then open http://127.0.0.1:8765.

## Workflow

1. **Source**: paste a link, set a rough start and end. The audio is fetched with a few seconds of padding on each side.
2. **Output folder**: choose where snippets are saved. Export stays disabled until this is set.
3. **Trim**: drag the region edges on the waveform to the exact start and end. Cuts are sample-accurate.
4. **Clean (optional)**: remove music, reverb or noise, then compare Original and Clean.
5. **Export**: writes a WAV plus an optional `.txt` transcript with the same name.

## What makes a good OmniVoice reference

- 3 to 10 seconds. Longer clips slow inference and can reduce cloning quality.
- One speaker, continuous speech, cut on complete words. Long silences are removed by OmniVoice anyway.
- Naturally clean audio beats cleaned-up audio. OmniVoice tolerates mild noise, so only run cleanup when you hear a real problem.
- The clip's pace and delivery carry into the generated voice.
- Use a clip in the language you will synthesize; cross-lingual cloning keeps the accent.
- Pass the exact transcript as `ref_text`. The draft button uses Whisper; check it against the audio.

Exports default to 24 kHz mono 16-bit WAV, which matches OmniVoice's output rate.

## Tests

```
uv run pytest
```

## Notes

- Downloaded clips live in `work/` and models in `models/`; both can be deleted at any time.
- Only use voices you have the right to use.
