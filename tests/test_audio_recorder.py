import sys
from types import SimpleNamespace
import wave

from ai_operator_controller.audio_recorder import record_microphone_to_wav
from ai_operator_controller.audio_recorder import summarize_audio_samples


def test_summarize_audio_samples_reports_safe_metadata_only():
    summary = summarize_audio_samples(
        [[0.0], [0.5], [-1.0], [1.0]],
        sample_rate=16000,
        dtype="float32",
    )

    assert summary.sample_rate == 16000
    assert summary.frame_count == 4
    assert summary.channel_count == 1
    assert summary.dtype == "float32"
    assert summary.duration_seconds == 0.00025
    assert round(summary.rms, 6) == 0.75
    assert summary.peak_abs == 1.0


def test_summarize_audio_samples_handles_empty_audio():
    summary = summarize_audio_samples([], sample_rate=16000, dtype="float32")

    assert summary.frame_count == 0
    assert summary.channel_count == 0
    assert summary.duration_seconds == 0
    assert summary.rms == 0
    assert summary.peak_abs == 0


def test_record_microphone_to_wav_writes_pcm_file(tmp_path, monkeypatch):
    output_path = tmp_path / "sample.wav"

    fake_sounddevice = SimpleNamespace(
        rec=lambda *args, **kwargs: [[0.0], [1.0], [-1.0]],
        wait=lambda: None,
    )
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)

    summary = record_microphone_to_wav(
        output_path,
        seconds=0.1,
        sample_rate=16000,
        channels=1,
    )

    assert summary.frame_count == 3
    assert summary.channel_count == 1
    assert summary.peak_abs == 1.0

    with wave.open(str(output_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 3
