from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ACTION_NAMES = frozenset(
    {
        "dictate_paste",
        "dictate_clipboard",
        "enter",
        "space",
        "backspace",
        "chat_next",
        "chat_previous",
        "cursor_down",
        "cursor_left",
        "cursor_right",
        "cursor_up",
        "focus_chat_list",
        "focus_message_pane",
        "mouse_left_click",
        "mouse_right_click",
        "scroll_down",
        "scroll_up",
        "ctrl_tab",
        "ctrl_shift_tab",
        "paste_clipboard",
        "copy_text",
    }
)

ACTION_KEYS = frozenset(
    {
        "action",
        "down_action",
        "left_action",
        "negative_action",
        "positive_action",
        "right_action",
        "up_action",
    }
)


def validate_action_name(action_name: str) -> str:
    if action_name not in ACTION_NAMES:
        raise ValueError(f"Unknown action: {action_name}")
    return action_name


def collect_profile_actions(profile: Mapping[str, Any]) -> set[str]:
    actions: set[str] = set()
    _collect_actions(profile, actions)
    return actions


def _collect_actions(value: Any, actions: set[str]) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if key in ACTION_KEYS and isinstance(nested_value, str):
                actions.add(validate_action_name(nested_value))
            else:
                _collect_actions(nested_value, actions)
    elif isinstance(value, list):
        for item in value:
            _collect_actions(item, actions)
