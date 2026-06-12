from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import math
from pathlib import Path
import struct
from typing import Any
import wave


@dataclass(frozen=True)
class AudioSampleSummary:
    sample_rate: int
    frame_count: int
    channel_count: int
    dtype: str
    duration_seconds: float
    rms: float
    peak_abs: float


class AudioRecorderError(RuntimeError):
    pass


def record_microphone_once(
    *,
    seconds: float,
    sample_rate: int = 16000,
    channels: int = 1,
    device: int | None = None,
) -> AudioSampleSummary:
    _validate_recording_options(seconds=seconds, sample_rate=sample_rate, channels=channels)
    samples = _record_microphone_samples(
        seconds=seconds,
        sample_rate=sample_rate,
        channels=channels,
        device=device,
    )
    dtype = str(getattr(samples, "dtype", "float32"))
    return summarize_audio_samples(samples, sample_rate=sample_rate, dtype=dtype)


def record_microphone_to_wav(
    output_path: str | Path,
    *,
    seconds: float,
    sample_rate: int = 16000,
    channels: int = 1,
    device: int | None = None,
) -> AudioSampleSummary:
    _validate_recording_options(seconds=seconds, sample_rate=sample_rate, channels=channels)
    samples = _record_microphone_samples(
        seconds=seconds,
        sample_rate=sample_rate,
        channels=channels,
        device=device,
    )
    dtype = str(getattr(samples, "dtype", "float32"))
    summary = summarize_audio_samples(samples, sample_rate=sample_rate, dtype=dtype)
    _write_float32_wav(Path(output_path), samples, sample_rate=sample_rate, channels=channels)
    return summary


def _record_microphone_samples(
    *,
    seconds: float,
    sample_rate: int,
    channels: int,
    device: int | None,
) -> Any:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise AudioRecorderError("sounddevice is not installed") from exc

    frame_count = max(1, int(round(seconds * sample_rate)))
    try:
        samples = sd.rec(
            frame_count,
            samplerate=sample_rate,
            channels=channels,
            dtype="float32",
            device=device,
        )
        sd.wait()
    except Exception as exc:
        raise AudioRecorderError(f"microphone recording failed: {exc}") from exc

    return samples


def summarize_audio_samples(
    samples: Any,
    *,
    sample_rate: int,
    dtype: str,
) -> AudioSampleSummary:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    rows = _rows_from_samples(samples)
    frame_count = len(rows)
    channel_count = _channel_count(rows)
    values = list(_flatten(rows))
    peak_abs = max((abs(value) for value in values), default=0.0)
    rms = math.sqrt(sum(value * value for value in values) / len(values)) if values else 0.0

    return AudioSampleSummary(
        sample_rate=sample_rate,
        frame_count=frame_count,
        channel_count=channel_count,
        dtype=dtype,
        duration_seconds=frame_count / sample_rate,
        rms=rms,
        peak_abs=peak_abs,
    )


def _validate_recording_options(*, seconds: float, sample_rate: int, channels: int) -> None:
    if seconds <= 0:
        raise ValueError("seconds must be positive")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if channels <= 0:
        raise ValueError("channels must be positive")


def _write_float32_wav(
    output_path: Path,
    samples: Any,
    *,
    sample_rate: int,
    channels: int,
) -> None:
    rows = _rows_from_samples(samples)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for row in rows:
            values = row if _is_channel_sequence(row) else [row]
            padded_values = list(values)[:channels]
            padded_values.extend([0.0] * (channels - len(padded_values)))
            for value in padded_values:
                wav_file.writeframesraw(_float_to_pcm16(float(value)))
        wav_file.writeframes(b"")


def _float_to_pcm16(value: float) -> bytes:
    clamped = max(-1.0, min(1.0, value))
    integer = int(round(clamped * 32767))
    return struct.pack("<h", integer)


def _rows_from_samples(samples: Any) -> list[Any]:
    if hasattr(samples, "tolist"):
        samples = samples.tolist()
    if samples is None:
        return []
    if isinstance(samples, Sequence) and not isinstance(samples, str):
        return list(samples)
    return list(samples)


def _channel_count(rows: list[Any]) -> int:
    if not rows:
        return 0
    first = rows[0]
    if _is_channel_sequence(first):
        return len(first)
    return 1


def _flatten(rows: Iterable[Any]) -> Iterable[float]:
    for row in rows:
        if _is_channel_sequence(row):
            for value in row:
                yield float(value)
        else:
            yield float(row)


def _is_channel_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)
