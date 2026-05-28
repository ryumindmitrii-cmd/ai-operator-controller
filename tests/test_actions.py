import json
from pathlib import Path

import pytest

from ai_operator_controller.actions import ACTION_NAMES, collect_profile_actions, validate_action_name


def test_public_codex_profile_uses_only_known_actions():
    profile = json.loads(Path("config/examples/profile.codex.windows.json").read_text())

    actions = collect_profile_actions(profile)

    assert {
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
        "scroll_down",
        "scroll_up",
    }.issubset(actions)
    assert actions <= ACTION_NAMES


def test_public_codex_profile_maps_controller_to_chat_cursor_and_scroll_actions():
    profile = json.loads(Path("config/examples/profile.codex.windows.json").read_text())

    axes = profile["gamepad"]["axes"]
    buttons = profile["gamepad"]["buttons"]
    hats = profile["gamepad"]["hats"]

    assert buttons["a"]["action"] == "dictate_paste"
    assert buttons["a"]["focus_before_action"] == {
        "target": "message_input",
        "strategy": "lower_center_click",
        "x_ratio": 0.5,
        "bottom_offset_pixels": 100,
        "move_caret_to_end": True,
    }
    assert buttons["b"]["repeat"] is True
    assert buttons["b"]["cooldown_seconds"] == 0.1
    assert axes["lt"]["action"] == "space"
    assert axes["left_stick_y"]["negative_action"] == "chat_previous"
    assert axes["left_stick_y"]["positive_action"] == "chat_next"
    assert axes["right_stick_x"]["negative_action"] == "cursor_left"
    assert axes["right_stick_x"]["positive_action"] == "cursor_right"
    assert axes["right_stick_y"]["negative_action"] == "cursor_up"
    assert axes["right_stick_y"]["positive_action"] == "cursor_down"
    assert hats["dpad"]["up_action"] == "scroll_up"
    assert hats["dpad"]["down_action"] == "scroll_down"
    assert hats["dpad"]["left_action"] == "focus_chat_list"
    assert hats["dpad"]["right_action"] == "focus_message_pane"
    assert hats["dpad"]["repeat"] is True


def test_validate_action_name_rejects_unknown_actions():
    with pytest.raises(ValueError, match="Unknown action"):
        validate_action_name("open_private_local_file")
