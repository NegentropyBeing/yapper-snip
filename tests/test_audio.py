import subprocess
import wave

import pytest

from app import audio


@pytest.fixture
def tone(tmp_path):
    path = tmp_path / "tone.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=10",
         "-ac", "2", "-af", "volume=0.25", "-c:a", "pcm_s16le", str(path)],
        check=True,
    )
    return path


def frames(path):
    with wave.open(str(path)) as w:
        return w.getnframes(), w.getframerate(), w.getnchannels()


@pytest.mark.parametrize("value, expected", [
    ("75", 75.0), ("75.5", 75.5), ("1:15", 75.0), ("00:01:15.250", 75.25),
    ("1:02:03", 3723.0), (12, 12.0), ("0,5", 0.5), ("", None), (None, None),
])
def test_parse_timestamp(value, expected):
    assert audio.parse_timestamp(value) == expected


@pytest.mark.parametrize("value", ["abc", "1:2:3:4", "-5", "1:-2", -1])
def test_parse_timestamp_rejects(value):
    with pytest.raises(ValueError):
        audio.parse_timestamp(value)


def test_cut_is_sample_accurate(tone, tmp_path):
    out = tmp_path / "cut.wav"
    audio.cut(tone, out, 1.2345, 4.5678)
    n, rate, channels = frames(out)
    assert (rate, channels) == (48000, 2)
    assert abs(n - round((4.5678 - 1.2345) * 48000)) <= 1


def test_cut_resample_mono_fade(tone, tmp_path):
    out = tmp_path / "cut.wav"
    audio.cut(tone, out, 2.0, 7.0, sample_rate=24000, mono=True, fade_ms=5)
    n, rate, channels = frames(out)
    assert (rate, channels) == (24000, 1)
    assert abs(n - 5 * 24000) <= 1


def test_cut_normalize(tone, tmp_path):
    out = tmp_path / "cut.wav"
    audio.cut(tone, out, 2.0, 5.0, normalize=True)
    assert audio.peak_db(out, 0, 3) == pytest.approx(audio.NORMALIZE_PEAK_DB, abs=0.2)


def test_cut_rejects_empty_range(tone, tmp_path):
    with pytest.raises(ValueError):
        audio.cut(tone, tmp_path / "cut.wav", 3.0, 3.0)
