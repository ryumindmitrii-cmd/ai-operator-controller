from __future__ import annotations

from dataclasses import dataclass

from .actions import validate_action_name


@dataclass(frozen=True)
class KeyboardAction:
    keys: tuple[str, ...]


class KeyboardActionPlanner:
    _KEYS_BY_ACTION = {
        "backspace": ("backspace",),
        "chat_next": ("ctrl", "tab"),
        "chat_previous": ("ctrl", "shift", "tab"),
        "ctrl_tab": ("ctrl", "tab"),
        "ctrl_shift_tab": ("ctrl", "shift", "tab"),
        "cursor_down": ("down",),
        "cursor_left": ("left",),
        "cursor_right": ("right",),
        "cursor_up": ("up",),
        "enter": ("enter",),
        "space": ("space",),
        "paste_clipboard": ("ctrl", "v"),
    }

    def plan(self, action_name: str) -> KeyboardAction:
        validate_action_name(action_name)
        try:
            return KeyboardAction(keys=self._KEYS_BY_ACTION[action_name])
        except KeyError as exc:
            raise ValueError(f"Action has no keyboard plan: {action_name}") from exc
