from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_profile, validate_profile


class CalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class WindowGeometry:
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class FocusRatios:
    x_ratio: float
    y_ratio: float


@dataclass(frozen=True)
class CapturedWindowPoint:
    window: WindowGeometry
    point_x: float
    point_y: float
    window_title: str | None = None


@dataclass(frozen=True)
class ProfileCalibrationResult:
    profile_path: Path
    target: str
    ratios: FocusRatios
    saved: bool
    source: str
    capture: CapturedWindowPoint | None = None


def ratios_from_window_point(
    window: WindowGeometry,
    *,
    point_x: float,
    point_y: float,
) -> FocusRatios:
    if window.width <= 0 or window.height <= 0:
        raise CalibrationError("window width and height must be positive")

    x_ratio = (point_x - window.left) / window.width
    y_ratio = (point_y - window.top) / window.height
    if not 0 <= x_ratio <= 1 or not 0 <= y_ratio <= 1:
        raise CalibrationError("calibration point must be inside the window")
    return FocusRatios(x_ratio=x_ratio, y_ratio=y_ratio)


def ratios_from_captured_window_point(capture: CapturedWindowPoint) -> FocusRatios:
    return ratios_from_window_point(
        capture.window,
        point_x=capture.point_x,
        point_y=capture.point_y,
    )


def capture_current_mouse_position() -> CapturedWindowPoint:
    if sys.platform != "win32":
        raise CalibrationError("current mouse capture requires Windows")

    import ctypes

    ga_root = 2

    class POINT(ctypes.Structure):
        _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))

    class RECT(ctypes.Structure):
        _fields_ = (
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        )

    user32 = ctypes.windll.user32
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        raise CalibrationError("failed to read current mouse position")

    hwnd = user32.WindowFromPoint(point)
    if hwnd:
        root_hwnd = user32.GetAncestor(hwnd, ga_root)
        if root_hwnd:
            hwnd = root_hwnd
    else:
        hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise CalibrationError("failed to read window under current mouse position")

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise CalibrationError("failed to read window rectangle")

    window_title = _get_window_title(user32, hwnd, ctypes)
    return CapturedWindowPoint(
        window=WindowGeometry(
            left=float(rect.left),
            top=float(rect.top),
            width=float(rect.right - rect.left),
            height=float(rect.bottom - rect.top),
        ),
        point_x=float(point.x),
        point_y=float(point.y),
        window_title=window_title,
    )


def calibrate_profile(
    profile: dict[str, Any],
    *,
    target: str,
    x_ratio: float,
    y_ratio: float,
) -> dict[str, Any]:
    if not target:
        raise CalibrationError("target must be non-empty")
    _validate_ratio("x_ratio", x_ratio)
    _validate_ratio("y_ratio", y_ratio)

    updated = copy.deepcopy(profile)
    focus_targets = updated.setdefault("focus_targets", {})
    if not isinstance(focus_targets, dict):
        raise CalibrationError("focus_targets must be an object")

    existing = focus_targets.get(target, {})
    if existing is not None and not isinstance(existing, dict):
        raise CalibrationError(f"focus target '{target}' must be an object")

    target_config: dict[str, Any] = {
        "strategy": "window_relative_click",
        "x_ratio": float(x_ratio),
        "y_ratio": float(y_ratio),
    }
    move_caret = existing.get("move_caret_to_end") if isinstance(existing, dict) else None
    if move_caret is None and target == "message_input":
        move_caret = _find_focus_before_action_move_caret(updated, target)
    if move_caret is not None:
        target_config["move_caret_to_end"] = bool(move_caret)

    focus_targets[target] = target_config
    _replace_inline_focus_before_actions_with_reference(updated, target)
    validate_profile(updated)
    return updated


def calibrate_profile_file(
    profile_path: Path,
    *,
    target: str,
    ratios: FocusRatios,
    write: bool,
    allow_nonlocal_profile: bool = False,
    source: str = "ratio",
    capture: CapturedWindowPoint | None = None,
) -> ProfileCalibrationResult:
    if write and not allow_nonlocal_profile and not is_local_profile_path(profile_path):
        raise CalibrationError(
            "refusing to write non-local profile; use config/local or pass "
            "--allow-nonlocal-profile"
        )

    profile = load_profile(profile_path)
    validate_profile(profile, source=profile_path)
    updated = calibrate_profile(
        profile,
        target=target,
        x_ratio=ratios.x_ratio,
        y_ratio=ratios.y_ratio,
    )

    if write:
        profile_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return ProfileCalibrationResult(
        profile_path=profile_path,
        target=target,
        ratios=ratios,
        saved=write,
        source=source,
        capture=capture,
    )


def is_local_profile_path(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    return any(parts[index : index + 2] == ("config", "local") for index in range(len(parts) - 1))


def format_profile_calibration(result: ProfileCalibrationResult) -> list[str]:
    lines = [
        "Profile calibration",
        f"Mode: {'write' if result.saved else 'dry-run'}",
        f"Profile: {result.profile_path}",
        f"Target: {result.target}",
        f"Source: {result.source}",
        "Strategy: window_relative_click",
        f"x_ratio: {result.ratios.x_ratio:.4f}",
        f"y_ratio: {result.ratios.y_ratio:.4f}",
        f"Saved: {'yes' if result.saved else 'no'}",
        "Safety: use config/local for machine-specific coordinates.",
    ]
    if result.capture is not None:
        window = result.capture.window
        lines.insert(
            5,
            "Window: "
            f"left={_format_number(window.left)} "
            f"top={_format_number(window.top)} "
            f"width={_format_number(window.width)} "
            f"height={_format_number(window.height)}",
        )
        lines.insert(
            6,
            f"Point: x={_format_number(result.capture.point_x)} "
            f"y={_format_number(result.capture.point_y)}",
        )
        if result.capture.window_title:
            lines.insert(7, "Window title: <hidden>")
    return lines


def _validate_ratio(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CalibrationError(f"{name} must be a number")
    if not 0 <= float(value) <= 1:
        raise CalibrationError(f"{name} must be between 0 and 1")


def _get_window_title(user32, hwnd, ctypes) -> str | None:
    title_length = user32.GetWindowTextLengthW(hwnd)
    if title_length <= 0:
        return None
    buffer = ctypes.create_unicode_buffer(title_length + 1)
    if not user32.GetWindowTextW(hwnd, buffer, len(buffer)):
        return None
    return buffer.value or None


def _format_number(value: float) -> str:
    return f"{value:g}"


def _find_focus_before_action_move_caret(profile: dict[str, Any], target: str) -> bool | None:
    buttons = profile.get("gamepad", {}).get("buttons", {})
    if not isinstance(buttons, dict):
        return None
    for binding in buttons.values():
        if not isinstance(binding, dict):
            continue
        focus = binding.get("focus_before_action")
        if not isinstance(focus, dict) or focus.get("target") != target:
            continue
        move_caret = focus.get("move_caret_to_end")
        if isinstance(move_caret, bool):
            return move_caret
    return None


def _replace_inline_focus_before_actions_with_reference(
    profile: dict[str, Any],
    target: str,
) -> None:
    buttons = profile.get("gamepad", {}).get("buttons", {})
    if not isinstance(buttons, dict):
        return
    for binding in buttons.values():
        if not isinstance(binding, dict):
            continue
        focus = binding.get("focus_before_action")
        if isinstance(focus, dict) and focus.get("target") == target:
            binding["focus_before_action"] = {"target": target}
