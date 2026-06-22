from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .actions import ACTION_KEYS, collect_profile_actions, validate_action_name


class ProfileValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ProfileValidationResult:
    profile_name: str
    actions: frozenset[str]
    button_count: int
    axis_count: int
    hat_count: int
    focus_target_count: int


_PRIVATE_MARKER_PATTERNS = (
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"(^|[\\/])\.env($|[\\/])", re.IGNORECASE),
    re.compile(r"\b(auth|credential|credentials|password|secret|token)\b", re.IGNORECASE),
    re.compile(r"\b(replacements\.json|transcripts?|recordings?|logs?)\b", re.IGNORECASE),
)


def load_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path)
    try:
        raw_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProfileValidationError(f"{profile_path}: cannot read profile: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProfileValidationError(f"{profile_path}: invalid JSON: {exc}") from exc

    if not isinstance(raw_profile, dict):
        raise ProfileValidationError(f"{profile_path}: profile must be a JSON object")
    return raw_profile


def validate_profile(
    profile: Mapping[str, Any],
    *,
    source: str | Path | None = None,
) -> ProfileValidationResult:
    label = _source_label(source)
    _reject_private_markers(profile, label)

    profile_name = _require_non_empty_str(profile, "profile_name", label)
    _validate_hotkeys(_require_mapping(profile, "hotkeys", label), label)

    focus_targets = _optional_mapping(profile, "focus_targets", label)
    focus_target_count = _validate_focus_targets(focus_targets, label)

    gamepad = _require_mapping(profile, "gamepad", label)
    _validate_optional_bool(gamepad, "enabled", label)
    _validate_optional_non_negative_int(gamepad, "index", label)

    buttons = _require_mapping(gamepad, "buttons", label)
    axes = _require_mapping(gamepad, "axes", label)
    hats = _require_mapping(gamepad, "hats", label)

    for name, binding in buttons.items():
        focus_target_count += _validate_button_binding(str(name), binding, focus_targets, label)
    for name, binding in axes.items():
        _validate_axis_binding(str(name), binding, label)
    for name, binding in hats.items():
        _validate_hat_binding(str(name), binding, label)

    try:
        actions = frozenset(collect_profile_actions(profile))
    except ValueError as exc:
        raise ProfileValidationError(f"{label}: {exc}") from exc

    return ProfileValidationResult(
        profile_name=profile_name,
        actions=actions,
        button_count=len(buttons),
        axis_count=len(axes),
        hat_count=len(hats),
        focus_target_count=focus_target_count,
    )


def _validate_hotkeys(hotkeys: Mapping[str, Any], label: str) -> None:
    for key in ("paste_dictation", "clipboard_dictation"):
        _require_non_empty_str(hotkeys, key, label)


def _validate_button_binding(
    name: str,
    value: Any,
    focus_targets: Mapping[str, Any],
    label: str,
) -> int:
    binding = _require_nested_mapping(value, f"gamepad.buttons.{name}", label)
    _require_non_negative_int(binding, "button", label)
    _require_action(binding, "action", label)
    _validate_optional_bool(binding, "repeat", label)
    _validate_optional_non_negative_number(binding, "cooldown_seconds", label)

    focus_before_action = binding.get("focus_before_action")
    if focus_before_action is None:
        return 0
    return _validate_focus_before_action(
        focus_before_action,
        f"gamepad.buttons.{name}",
        focus_targets,
        label,
    )


def _validate_axis_binding(name: str, value: Any, label: str) -> None:
    binding = _require_nested_mapping(value, f"gamepad.axes.{name}", label)
    _require_non_negative_int(binding, "axis", label)
    threshold = _require_number(binding, "threshold", label)
    release_threshold = _require_number(binding, "release_threshold", label)
    if not 0 < release_threshold < threshold <= 1:
        raise ProfileValidationError(
            f"{label}: gamepad.axes.{name} thresholds must satisfy "
            "0 < release_threshold < threshold <= 1"
        )
    _require_non_negative_number(binding, "cooldown_seconds", label)
    _validate_optional_bool(binding, "repeat", label)
    _validate_optional_bool(binding, "scale_cooldown_by_intensity", label)
    _require_at_least_one_action(
        binding,
        ("action", "negative_action", "positive_action"),
        f"gamepad.axes.{name}",
        label,
    )
    _validate_action_fields(binding, label)


def _validate_hat_binding(name: str, value: Any, label: str) -> None:
    binding = _require_nested_mapping(value, f"gamepad.hats.{name}", label)
    _require_non_negative_int(binding, "hat", label)
    _require_non_negative_number(binding, "cooldown_seconds", label)
    _validate_optional_bool(binding, "repeat", label)
    _require_at_least_one_action(
        binding,
        ("left_action", "right_action", "up_action", "down_action"),
        f"gamepad.hats.{name}",
        label,
    )
    _validate_action_fields(binding, label)


def _validate_focus_targets(focus_targets: Mapping[str, Any], label: str) -> int:
    for name, target in focus_targets.items():
        if not isinstance(name, str) or not name:
            raise ProfileValidationError(f"{label}: focus target names must be non-empty strings")
        _validate_focus_target_descriptor(target, f"focus_targets.{name}", label)
    return len(focus_targets)


def _validate_focus_before_action(
    value: Any,
    path: str,
    focus_targets: Mapping[str, Any],
    label: str,
) -> int:
    focus = _require_nested_mapping(value, f"{path}.focus_before_action", label)
    target = _require_non_empty_str(focus, "target", label)
    if target != "message_input":
        raise ProfileValidationError(
            f"{label}: {path}.focus_before_action.target must be 'message_input', "
            f"got '{target}'"
        )

    has_inline_descriptor = any(key != "target" for key in focus)
    if not has_inline_descriptor:
        if target not in focus_targets:
            raise ProfileValidationError(
                f"{label}: {path}.focus_before_action.target '{target}' "
                "must exist in focus_targets or define an inline descriptor"
            )
        return 0

    _validate_focus_target_descriptor(focus, f"{path}.focus_before_action", label)
    return 1


def _validate_focus_target_descriptor(value: Any, path: str, label: str) -> None:
    focus = _require_nested_mapping(value, path, label)
    strategy = _require_non_empty_str(focus, "strategy", label)
    if strategy == "window_relative_click":
        x_ratio = _require_number(focus, "x_ratio", label)
        if not 0 <= x_ratio <= 1:
            raise ProfileValidationError(f"{label}: {path}.x_ratio must be between 0 and 1")
        y_ratio = _require_number(focus, "y_ratio", label)
        if not 0 <= y_ratio <= 1:
            raise ProfileValidationError(f"{label}: {path}.y_ratio must be between 0 and 1")
    elif strategy == "lower_center_click":
        x_ratio = _require_number(focus, "x_ratio", label)
        if not 0 <= x_ratio <= 1:
            raise ProfileValidationError(f"{label}: {path}.x_ratio must be between 0 and 1")
        _require_non_negative_int(focus, "bottom_offset_pixels", label)
    else:
        raise ProfileValidationError(
            f"{label}: {path}.strategy must be 'window_relative_click' or 'lower_center_click'"
        )

    if "move_caret_to_end" in focus:
        _require_bool(focus, "move_caret_to_end", label)


def _validate_action_fields(mapping: Mapping[str, Any], label: str) -> None:
    for key, value in mapping.items():
        if key in ACTION_KEYS and value is not None:
            if not isinstance(value, str) or not value:
                raise ProfileValidationError(f"{label}: {key} must be a non-empty action name")
            try:
                validate_action_name(value)
            except ValueError as exc:
                raise ProfileValidationError(f"{label}: {exc}") from exc


def _require_action(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = _require_non_empty_str(mapping, key, label)
    try:
        validate_action_name(value)
    except ValueError as exc:
        raise ProfileValidationError(f"{label}: {exc}") from exc
    return value


def _require_at_least_one_action(
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
    path: str,
    label: str,
) -> None:
    if not any(key in mapping and mapping[key] is not None for key in keys):
        joined = ", ".join(keys)
        raise ProfileValidationError(f"{label}: {path} must define at least one of: {joined}")


def _reject_private_markers(value: Any, label: str) -> None:
    for text in _iter_strings(value):
        if any(pattern.search(text) for pattern in _PRIVATE_MARKER_PATTERNS):
            raise ProfileValidationError(f"{label}: private/local marker detected in profile")


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


def _source_label(source: str | Path | None) -> str:
    if source is None:
        return "profile"
    return str(source)


def _require_mapping(mapping: Mapping[str, Any], key: str, label: str) -> Mapping[str, Any]:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise ProfileValidationError(f"{label}: missing required object '{key}'") from exc
    return _require_nested_mapping(value, key, label)


def _optional_mapping(mapping: Mapping[str, Any], key: str, label: str) -> Mapping[str, Any]:
    if key not in mapping:
        return {}
    return _require_nested_mapping(mapping[key], key, label)


def _require_nested_mapping(value: Any, path: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileValidationError(f"{label}: {path} must be an object")
    return value


def _require_non_empty_str(mapping: Mapping[str, Any], key: str, label: str) -> str:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise ProfileValidationError(f"{label}: missing required string '{key}'") from exc
    if not isinstance(value, str) or not value:
        raise ProfileValidationError(f"{label}: {key} must be a non-empty string")
    return value


def _require_bool(mapping: Mapping[str, Any], key: str, label: str) -> bool:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise ProfileValidationError(f"{label}: missing required boolean '{key}'") from exc
    if not isinstance(value, bool):
        raise ProfileValidationError(f"{label}: {key} must be a boolean")
    return value


def _validate_optional_bool(mapping: Mapping[str, Any], key: str, label: str) -> None:
    if key in mapping:
        _require_bool(mapping, key, label)


def _require_non_negative_int(mapping: Mapping[str, Any], key: str, label: str) -> int:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise ProfileValidationError(f"{label}: missing required integer '{key}'") from exc
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProfileValidationError(f"{label}: {key} must be a non-negative integer")
    return value


def _validate_optional_non_negative_int(
    mapping: Mapping[str, Any],
    key: str,
    label: str,
) -> None:
    if key in mapping:
        _require_non_negative_int(mapping, key, label)


def _require_number(mapping: Mapping[str, Any], key: str, label: str) -> float:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise ProfileValidationError(f"{label}: missing required number '{key}'") from exc
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ProfileValidationError(f"{label}: {key} must be a number")
    return float(value)


def _require_non_negative_number(mapping: Mapping[str, Any], key: str, label: str) -> float:
    value = _require_number(mapping, key, label)
    if value < 0:
        raise ProfileValidationError(f"{label}: {key} must be non-negative")
    return value


def _validate_optional_non_negative_number(
    mapping: Mapping[str, Any],
    key: str,
    label: str,
) -> None:
    if key in mapping:
        _require_non_negative_number(mapping, key, label)
