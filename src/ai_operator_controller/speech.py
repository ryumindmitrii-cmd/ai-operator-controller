from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class SpeechConfigError(ValueError):
    pass


class SpeechRecognitionError(RuntimeError):
    pass


class WhisperModelFactory(Protocol):
    def __call__(
        self,
        model_size_or_path: str,
        *,
        device: str,
        compute_type: str,
        local_files_only: bool,
    ) -> Any:
        pass


@dataclass(frozen=True)
class SpeechConfig:
    profile_name: str
    backend: str
    model: str
    device: str
    compute_type: str
    language: str | None
    vad_filter: bool
    initial_prompt: str | None
    hotwords: tuple[str, ...]
    fallback_enabled: bool
    fallback_device: str | None
    fallback_compute_type: str | None


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    language_probability: float | None
    duration_seconds: float | None
    segment_count: int
    model: str
    device: str
    compute_type: str
    vad_filter: bool
    used_fallback: bool


_PRIVATE_MARKER_PATTERNS = (
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"(^|[\\/])\.env($|[\\/])", re.IGNORECASE),
    re.compile(r"\b(auth|credential|credentials|password|secret|token)\b", re.IGNORECASE),
    re.compile(r"\b(replacements\.json|transcripts?|recordings?|logs?)\b", re.IGNORECASE),
)


def load_speech_config(path: str | Path) -> SpeechConfig:
    config_path = Path(path)
    try:
        raw_config = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SpeechConfigError(f"{config_path}: cannot read speech profile: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SpeechConfigError(f"{config_path}: invalid JSON: {exc}") from exc

    if not isinstance(raw_config, Mapping):
        raise SpeechConfigError(f"{config_path}: speech profile must be a JSON object")

    label = str(config_path)
    _reject_private_markers(raw_config, label)

    backend = _require_non_empty_str(raw_config, "backend", label)
    if backend != "faster-whisper":
        raise SpeechConfigError(f"{label}: backend must be 'faster-whisper'")

    fallback = raw_config.get("fallback", {})
    if fallback is None:
        fallback = {}
    if not isinstance(fallback, Mapping):
        raise SpeechConfigError(f"{label}: fallback must be an object")

    fallback_enabled = bool(fallback.get("enabled", False))
    fallback_device = _optional_non_empty_str(fallback, "device", label)
    fallback_compute_type = _optional_non_empty_str(fallback, "compute_type", label)

    return SpeechConfig(
        profile_name=_require_non_empty_str(raw_config, "profile_name", label),
        backend=backend,
        model=_require_non_empty_str(raw_config, "model", label),
        device=_require_non_empty_str(raw_config, "device", label),
        compute_type=_require_non_empty_str(raw_config, "compute_type", label),
        language=_normalize_language(_optional_non_empty_str(raw_config, "language", label)),
        vad_filter=_optional_bool(raw_config, "vad_filter", default=True, label=label),
        initial_prompt=_optional_non_empty_str(raw_config, "initial_prompt", label),
        hotwords=tuple(_list_of_strings(raw_config.get("hotwords", []), "hotwords", label)),
        fallback_enabled=fallback_enabled,
        fallback_device=fallback_device,
        fallback_compute_type=fallback_compute_type,
    )


def transcribe_audio_file(
    audio_path: str | Path,
    config: SpeechConfig,
    *,
    local_files_only: bool = True,
    model_factory: WhisperModelFactory | None = None,
) -> TranscriptionResult:
    source_path = Path(audio_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    factory = model_factory or _load_faster_whisper_model
    try:
        return _transcribe_with_device(
            source_path,
            config,
            factory,
            device=config.device,
            compute_type=config.compute_type,
            local_files_only=local_files_only,
            used_fallback=False,
        )
    except Exception as primary_exc:
        if not _can_try_fallback(config):
            raise SpeechRecognitionError(f"local transcription failed: {primary_exc}") from primary_exc
        try:
            return _transcribe_with_device(
                source_path,
                config,
                factory,
                device=config.fallback_device or config.device,
                compute_type=config.fallback_compute_type or config.compute_type,
                local_files_only=local_files_only,
                used_fallback=True,
            )
        except Exception as fallback_exc:
            raise SpeechRecognitionError(
                f"local transcription failed; fallback also failed: {fallback_exc}"
            ) from fallback_exc


def _transcribe_with_device(
    audio_path: Path,
    config: SpeechConfig,
    model_factory: WhisperModelFactory,
    *,
    device: str,
    compute_type: str,
    local_files_only: bool,
    used_fallback: bool,
) -> TranscriptionResult:
    model = model_factory(
        config.model,
        device=device,
        compute_type=compute_type,
        local_files_only=local_files_only,
    )
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=config.language,
        initial_prompt=config.initial_prompt,
        hotwords=" ".join(config.hotwords) if config.hotwords else None,
        vad_filter=config.vad_filter,
    )
    segments = list(segments_iter)
    text = "".join(str(getattr(segment, "text", "")) for segment in segments).strip()

    return TranscriptionResult(
        text=text,
        language=getattr(info, "language", None),
        language_probability=getattr(info, "language_probability", None),
        duration_seconds=getattr(info, "duration", None),
        segment_count=len(segments),
        model=config.model,
        device=device,
        compute_type=compute_type,
        vad_filter=config.vad_filter,
        used_fallback=used_fallback,
    )


def _load_faster_whisper_model(
    model_size_or_path: str,
    *,
    device: str,
    compute_type: str,
    local_files_only: bool,
) -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SpeechRecognitionError("faster-whisper is not installed") from exc

    return WhisperModel(
        model_size_or_path,
        device=device,
        compute_type=compute_type,
        local_files_only=local_files_only,
    )


def _can_try_fallback(config: SpeechConfig) -> bool:
    if not config.fallback_enabled:
        return False
    fallback_device = config.fallback_device or config.device
    fallback_compute_type = config.fallback_compute_type or config.compute_type
    return (fallback_device, fallback_compute_type) != (config.device, config.compute_type)


def _normalize_language(value: str | None) -> str | None:
    if value is None or value == "auto":
        return None
    return value


def _reject_private_markers(value: Any, label: str) -> None:
    for text in _iter_strings(value):
        if any(pattern.search(text) for pattern in _PRIVATE_MARKER_PATTERNS):
            raise SpeechConfigError(f"{label}: private/local marker detected in speech profile")


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for nested_value in value.values():
            strings.extend(_iter_strings(nested_value))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_iter_strings(item))
        return strings
    return []


def _require_non_empty_str(mapping: Mapping[str, Any], key: str, label: str) -> str:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise SpeechConfigError(f"{label}: missing required string '{key}'") from exc
    if not isinstance(value, str) or not value:
        raise SpeechConfigError(f"{label}: {key} must be a non-empty string")
    return value


def _optional_non_empty_str(mapping: Mapping[str, Any], key: str, label: str) -> str | None:
    if key not in mapping:
        return None
    value = mapping[key]
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise SpeechConfigError(f"{label}: {key} must be a non-empty string")
    return value


def _optional_bool(mapping: Mapping[str, Any], key: str, *, default: bool, label: str) -> bool:
    if key not in mapping:
        return default
    value = mapping[key]
    if not isinstance(value, bool):
        raise SpeechConfigError(f"{label}: {key} must be a boolean")
    return value


def _list_of_strings(value: Any, key: str, label: str) -> Sequence[str]:
    if not isinstance(value, list):
        raise SpeechConfigError(f"{label}: {key} must be a list")
    if not all(isinstance(item, str) and item for item in value):
        raise SpeechConfigError(f"{label}: {key} must contain only non-empty strings")
    return value
