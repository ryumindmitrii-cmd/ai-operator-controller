from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import importlib
import os
import platform
import sys
from pathlib import Path
from typing import Any, Literal

from . import __version__
from .config import load_profile, validate_profile
from .speech import SpeechConfig, load_speech_config


CheckStatus = Literal["ok", "warning", "error"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    detail: str
    next_step: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[CheckResult, ...]
    next_steps: tuple[str, ...] = ()

    @property
    def has_errors(self) -> bool:
        return any(check.status == "error" for check in self.checks)


@dataclass(frozen=True)
class AudioInputDevice:
    index: int
    name: str
    channels: int
    default_samplerate: float


def build_doctor_report(
    *,
    profile_path: Path | None,
    speech_profile_path: Path,
    mic_device: int | None,
    gamepad_index: int | None,
) -> DoctorReport:
    checks = [
        probe_package(),
        probe_audio_devices(mic_device=mic_device),
        probe_speech_profile(speech_profile_path),
        probe_speech_runtime(speech_profile_path),
        probe_gamepad(gamepad_index=gamepad_index),
    ]
    if profile_path is not None:
        checks.append(probe_profile(profile_path))

    next_steps = (
        "Use record-once --dry-run for metadata-only microphone level checks.",
        "Use dictate-run --dry-run before --execute-output.",
        "Use listen-gamepad --dry-run with --profile before enabling live controls.",
    )
    return DoctorReport(checks=tuple(checks), next_steps=next_steps)


def format_doctor_report(report: DoctorReport) -> list[str]:
    lines = [
        "AI Operator Controller doctor",
        "Mode: read-only diagnostics",
        "Safety: No audio was recorded. No clipboard or keyboard output was sent.",
    ]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.name}: {check.detail}")
        if check.next_step:
            lines.append(f"  Next: {check.next_step}")
    if report.next_steps:
        lines.append("Recommended next steps:")
        for next_step in report.next_steps:
            lines.append(f"- {next_step}")
    return lines


def probe_package() -> CheckResult:
    python_version = ".".join(str(part) for part in sys.version_info[:3])
    detail = (
        f"ai-operator-controller {__version__}; "
        f"Python {python_version}; platform {platform.system()} {platform.release()}"
    )
    return CheckResult("Package", "ok", detail)


def probe_audio_devices(
    *,
    mic_device: int | None,
    sounddevice_module: Any | None = None,
) -> CheckResult:
    try:
        sd = sounddevice_module or importlib.import_module("sounddevice")
    except ImportError as exc:
        return CheckResult(
            "Audio",
            "error",
            f"sounddevice is not installed: {exc}",
            'Install dependencies with python -m pip install -e ".[dev]".',
        )

    try:
        devices = _audio_input_devices(sd.query_devices())
        default_input = _default_input_index(getattr(sd, "default", None))
    except Exception as exc:
        return CheckResult(
            "Audio",
            "error",
            f"failed to query audio devices: {exc}",
            "Check Windows microphone permissions and audio drivers.",
        )

    if not devices:
        return CheckResult(
            "Audio",
            "warning",
            "no input devices detected",
            "Connect or enable a microphone, then rerun doctor.",
        )

    selected_index = mic_device if mic_device is not None else default_input
    default_device = _find_audio_device(devices, default_input)
    selected_device = _find_audio_device(devices, selected_index)
    device_list = ", ".join(
        f"{device.index}:{device.name} ({device.channels}ch)"
        for device in devices[:6]
    )
    if len(devices) > 6:
        device_list += f", +{len(devices) - 6} more"

    if selected_index is None:
        detail = (
            f"input devices: {len(devices)}; default: {_describe_audio_device(default_device)}; "
            f"selected: not specified; devices: {device_list}"
        )
        return CheckResult(
            "Audio",
            "ok",
            detail,
            "Use --mic-device <INDEX> if Windows has no default input or chooses the wrong mic.",
        )

    if selected_device is None:
        detail = (
            f"input devices: {len(devices)}; default: {_describe_audio_device(default_device)}; "
            f"selected input {selected_index} not found; devices: {device_list}"
        )
        return CheckResult(
            "Audio",
            "warning",
            detail,
            "Run doctor without --mic-device or choose a listed input device index.",
        )

    detail = (
        f"input devices: {len(devices)}; default: {_describe_audio_device(default_device)}; "
        f"selected: {_describe_audio_device(selected_device)}; devices: {device_list}"
    )
    return CheckResult("Audio", "ok", detail)


def probe_speech_profile(path: Path) -> CheckResult:
    config = load_speech_config(path)
    detail = _describe_speech_config(config)
    return CheckResult("Speech profile", "ok", detail)


def probe_speech_runtime(path: Path) -> CheckResult:
    config = load_speech_config(path)

    faster_whisper_spec = importlib.util.find_spec("faster_whisper")
    if faster_whisper_spec is None:
        return CheckResult(
            "Speech runtime",
            "error",
            "faster-whisper is not installed",
            'Install dependencies with python -m pip install -e ".[dev]".',
        )

    ctranslate2_spec = importlib.util.find_spec("ctranslate2")
    if ctranslate2_spec is None:
        return CheckResult(
            "Speech runtime",
            "error",
            "ctranslate2 is not installed",
            'Install dependencies with python -m pip install -e ".[dev]".',
        )

    try:
        import ctranslate2
    except Exception as exc:
        return CheckResult(
            "Speech runtime",
            "error",
            f"ctranslate2 import failed: {exc}",
            "Reinstall faster-whisper dependencies.",
        )

    cuda_count = _cuda_device_count(ctranslate2)
    compute_types = _supported_compute_types(ctranslate2, config.device)
    version = getattr(ctranslate2, "__version__", "unknown")
    detail = (
        f"faster-whisper available; ctranslate2 {version}; "
        f"configured device: {config.device}/{config.compute_type}; "
        f"cuda devices: {cuda_count}; supported compute: {_format_compute_types(compute_types)}"
    )

    if config.device == "cuda" and cuda_count <= 0:
        next_step = "Use a CUDA-capable machine or switch the local speech profile to CPU fallback."
        return CheckResult("Speech runtime", "warning", detail, next_step)
    if compute_types and config.compute_type not in compute_types:
        next_step = "Choose a compute_type supported by this CTranslate2 device."
        return CheckResult("Speech runtime", "warning", detail, next_step)
    return CheckResult("Speech runtime", "ok", detail)


def probe_gamepad(
    *,
    gamepad_index: int | None,
    pygame_module: Any | None = None,
) -> CheckResult:
    try:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        pygame = pygame_module or importlib.import_module("pygame")
    except ImportError as exc:
        return CheckResult(
            "Gamepad",
            "warning",
            f"pygame is not installed: {exc}",
            'Install dependencies with python -m pip install -e ".[dev]".',
        )

    selected_index = 0 if gamepad_index is None else gamepad_index
    try:
        pygame.init()
        pygame.joystick.init()
        if hasattr(pygame, "event"):
            pygame.event.pump()
        count = int(pygame.joystick.get_count())
        if count <= 0:
            return CheckResult(
                "Gamepad",
                "warning",
                "detected: 0",
                "Connect an Xbox-compatible controller, then rerun doctor.",
            )
        if selected_index < 0 or selected_index >= count:
            return CheckResult(
                "Gamepad",
                "warning",
                f"detected: {count}; selected index {selected_index} unavailable",
                "Run doctor without --gamepad-index or choose an available controller index.",
            )
        joystick = pygame.joystick.Joystick(selected_index)
        name = str(joystick.get_name())
        return CheckResult(
            "Gamepad",
            "ok",
            f"detected: {count}; selected: {selected_index} {name}",
        )
    except Exception as exc:
        return CheckResult(
            "Gamepad",
            "warning",
            f"failed to query gamepad devices: {exc}",
            "Reconnect the controller or try a different --gamepad-index.",
        )
    finally:
        with suppress(Exception):
            pygame.joystick.quit()
        with suppress(Exception):
            pygame.quit()


def probe_profile(path: Path) -> CheckResult:
    profile = load_profile(path)
    result = validate_profile(profile, source=path)
    detail = (
        f"{result.profile_name}; Actions: valid ({len(result.actions)}); "
        "Gamepad mapping: valid "
        f"({result.button_count} buttons, {result.axis_count} axes, {result.hat_count} hats); "
        f"Focus targets: valid ({result.focus_target_count}); "
        "Private/local markers: none detected"
    )
    return CheckResult("Profile", "ok", detail)


def _audio_input_devices(raw_devices: Any) -> tuple[AudioInputDevice, ...]:
    devices = []
    for index, raw_device in enumerate(raw_devices):
        channels = int(raw_device.get("max_input_channels", 0))
        if channels <= 0:
            continue
        devices.append(
            AudioInputDevice(
                index=index,
                name=str(raw_device.get("name", "unknown")),
                channels=channels,
                default_samplerate=float(raw_device.get("default_samplerate", 0.0)),
            )
        )
    return tuple(devices)


def _default_input_index(default_object: Any) -> int | None:
    if default_object is None:
        return None
    device_value = getattr(default_object, "device", None)
    if isinstance(device_value, int):
        return device_value
    if isinstance(device_value, (list, tuple)) and device_value:
        try:
            return int(device_value[0])
        except (TypeError, ValueError):
            return None
    return None


def _find_audio_device(
    devices: tuple[AudioInputDevice, ...],
    index: int | None,
) -> AudioInputDevice | None:
    if index is None:
        return None
    return next((device for device in devices if device.index == index), None)


def _describe_audio_device(device: AudioInputDevice | None) -> str:
    if device is None:
        return "unknown"
    return f"{device.index} {device.name} ({device.channels}ch @{device.default_samplerate:g}Hz)"


def _describe_speech_config(config: SpeechConfig) -> str:
    language = config.language or "auto"
    vad = "enabled" if config.vad_filter else "disabled"
    fallback = "enabled" if config.fallback_enabled else "disabled"
    return (
        f"{config.profile_name}; backend: {config.backend}; model: {config.model}; "
        f"device: {config.device}; compute: {config.compute_type}; language: {language}; "
        f"VAD: {vad}; fallback: {fallback}"
    )


def _cuda_device_count(ctranslate2: Any) -> int:
    getter = getattr(ctranslate2, "get_cuda_device_count", None)
    if getter is None:
        return 0
    try:
        return int(getter())
    except Exception:
        return 0


def _supported_compute_types(ctranslate2: Any, device: str) -> tuple[str, ...]:
    getter = getattr(ctranslate2, "get_supported_compute_types", None)
    if getter is None:
        return ()
    try:
        return tuple(sorted(str(value) for value in getter(device)))
    except Exception:
        return ()


def _format_compute_types(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "unknown"
