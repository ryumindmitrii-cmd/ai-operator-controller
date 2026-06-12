from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_operator_controller.speech import (
    SpeechConfigError,
    load_speech_config,
    transcribe_audio_file,
)


CONFIG_PATH = Path("config/examples/speech.local-quality.example.json")


def test_load_speech_config_reads_public_quality_profile():
    config = load_speech_config(CONFIG_PATH)

    assert config.profile_name == "local_quality_default"
    assert config.backend == "faster-whisper"
    assert config.model == "large-v3"
    assert config.device == "cuda"
    assert config.compute_type == "float16"
    assert config.language is None
    assert config.vad_filter is True
    assert "Codex" in config.hotwords
    assert config.fallback_enabled is True
    assert config.fallback_device == "cpu"
    assert config.fallback_compute_type == "int8"


def test_load_speech_config_rejects_private_markers(tmp_path):
    config_path = tmp_path / "speech.json"
    config_path.write_text(
        '{"profile_name":"bad","backend":"faster-whisper","model":"X:\\\\private",'
        '"device":"cpu","compute_type":"int8"}',
        encoding="utf-8",
    )

    with pytest.raises(SpeechConfigError, match="private/local marker"):
        load_speech_config(config_path)


def test_transcribe_audio_file_uses_faster_whisper_config_without_model_download(tmp_path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"not a real wav")
    calls = []

    class FakeWhisperModel:
        def __init__(self, *args, **kwargs):
            calls.append(("init", args, kwargs))

        def transcribe(self, *args, **kwargs):
            calls.append(("transcribe", args, kwargs))
            segments = [
                SimpleNamespace(text=" Hello", start=0.0, end=0.4),
                SimpleNamespace(text=" world", start=0.4, end=0.8),
            ]
            info = SimpleNamespace(language="en", language_probability=0.91, duration=0.8)
            return segments, info

    result = transcribe_audio_file(
        audio_path,
        load_speech_config(CONFIG_PATH),
        model_factory=FakeWhisperModel,
    )

    assert result.text == "Hello world"
    assert result.language == "en"
    assert result.language_probability == 0.91
    assert result.duration_seconds == 0.8
    assert result.segment_count == 2
    assert result.vad_filter is True
    assert calls[0] == (
        "init",
        ("large-v3",),
        {
            "device": "cuda",
            "compute_type": "float16",
            "local_files_only": True,
        },
    )
    assert calls[1] == (
        "transcribe",
        (str(audio_path),),
        {
            "language": None,
            "initial_prompt": load_speech_config(CONFIG_PATH).initial_prompt,
            "hotwords": "Codex ChatGPT GitHub PowerShell faster-whisper SendInput Python pytest Windows",
            "vad_filter": True,
        },
    )


def test_transcribe_audio_file_rejects_missing_audio_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        transcribe_audio_file(tmp_path / "missing.wav", load_speech_config(CONFIG_PATH))
