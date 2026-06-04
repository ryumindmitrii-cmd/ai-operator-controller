from __future__ import annotations

from dataclasses import dataclass

from .actions import validate_action_name


@dataclass(frozen=True)
class KeyboardAction:
    keys: tuple[str, ...] = ()
    scroll_clicks: float = 0
    mouse_target: str | None = None
    mouse_button: str | None = None
    click: bool = False


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
        "toggle_bottom_panel": ("ctrl", "j"),
        "toggle_sidebar": ("ctrl", "alt", "b"),
    }
    _SCROLL_CLICKS_BY_ACTION = {
        "scroll_down": -0.25,
        "scroll_up": 0.25,
    }
    _MOUSE_TARGET_BY_ACTION = {
        "focus_chat_list": ("chat_list", False),
        "focus_message_pane": ("message_pane", True),
    }
    _MOUSE_BUTTON_BY_ACTION = {
        "mouse_left_click": "left",
        "mouse_right_click": "right",
    }

    def plan(self, action_name: str) -> KeyboardAction:
        validate_action_name(action_name)
        if action_name in self._SCROLL_CLICKS_BY_ACTION:
            return KeyboardAction(scroll_clicks=self._SCROLL_CLICKS_BY_ACTION[action_name])
        if action_name in self._MOUSE_TARGET_BY_ACTION:
            mouse_target, click = self._MOUSE_TARGET_BY_ACTION[action_name]
            return KeyboardAction(mouse_target=mouse_target, click=click)
        if action_name in self._MOUSE_BUTTON_BY_ACTION:
            return KeyboardAction(mouse_button=self._MOUSE_BUTTON_BY_ACTION[action_name])
        try:
            return KeyboardAction(keys=self._KEYS_BY_ACTION[action_name])
        except KeyError as exc:
            raise ValueError(f"Action has no keyboard plan: {action_name}") from exc
