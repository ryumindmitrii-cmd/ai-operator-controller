from pathlib import Path

from ai_operator_controller.config import load_profile
from ai_operator_controller.gamepad import (
    GamepadActionRuntime,
    bindings_from_profile,
)


PROFILE_PATH = Path("config/examples/profile.codex.windows.json")


def _runtime() -> GamepadActionRuntime:
    return GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))


def _descriptions(result):
    assert result is not None
    return [event.describe() for event in result.output_events]


def test_profile_builds_gamepad_bindings():
    bindings = bindings_from_profile(load_profile(PROFILE_PATH))

    assert sorted(bindings.buttons) == ["a", "b", "lb", "menu", "rb", "x", "y"]
    assert sorted(bindings.axes) == [
        "left_stick_y",
        "lt",
        "right_stick_x",
        "right_stick_y",
        "rt",
    ]
    assert sorted(bindings.hats) == ["dpad"]
    assert bindings.buttons["b"].repeat is True


def test_runtime_button_repeats_when_held_after_cooldown():
    runtime = _runtime()

    first = runtime.update_button("b", True, now=0.0)
    blocked = runtime.update_button("b", True, now=0.05)
    repeated = runtime.update_button("b", True, now=0.1)

    assert first is not None
    assert first.action_name == "backspace"
    assert _descriptions(first) == ["press_keys: backspace"]
    assert blocked is None
    assert repeated is not None
    assert repeated.action_name == "backspace"


def test_runtime_buttons_emit_documented_codex_actions_and_dry_run_output():
    cases = [
        ("b", "backspace", ["press_keys: backspace"]),
        ("lb", "mouse_left_click", ["click_mouse: left"]),
        ("rb", "mouse_right_click", ["click_mouse: right"]),
        ("y", "toggle_sidebar", ["press_keys: ctrl+alt+b"]),
        ("menu", "toggle_bottom_panel", ["press_keys: ctrl+j"]),
    ]

    for button_name, action_name, expected_output in cases:
        result = _runtime().update_button(button_name, True, now=0.0)

        assert result is not None
        assert result.action_name == action_name
        assert _descriptions(result) == expected_output


def test_runtime_dictation_buttons_are_declared_without_dry_run_output_effect():
    profile = load_profile(PROFILE_PATH)

    a_result = _runtime().update_button("a", True, now=0.0)
    x_result = _runtime().update_button("x", True, now=0.0)

    for result in (a_result, x_result):
        assert result is not None
        assert result.action_name == "dictate_paste"
        assert result.output_events == ()
        assert result.unsupported_reason == "Action has no keyboard plan: dictate_paste"

    buttons = profile["gamepad"]["buttons"]
    assert buttons["a"]["focus_before_action"] == {
        "target": "message_input",
        "strategy": "lower_center_click",
        "x_ratio": 0.5,
        "bottom_offset_pixels": 100,
        "move_caret_to_end": True,
    }
    assert "focus_before_action" not in buttons["x"]


def test_runtime_triggers_emit_space_and_enter_dry_run_output():
    cases = [
        ("lt", 0.8, "space", ["press_keys: space"]),
        ("rt", 0.8, "enter", ["press_keys: enter"]),
    ]

    for axis_name, value, action_name, expected_output in cases:
        result = _runtime().update_axis(axis_name, value, now=0.0)

        assert result is not None
        assert result.action_name == action_name
        assert _descriptions(result) == expected_output


def test_runtime_left_stick_emits_chat_navigation_dry_run_output():
    runtime = _runtime()

    previous_chat = runtime.update_axis("left_stick_y", -0.8, now=0.0)
    runtime.update_axis("left_stick_y", 0.0, now=0.1)
    next_chat = runtime.update_axis("left_stick_y", 0.8, now=0.5)

    assert previous_chat is not None
    assert previous_chat.action_name == "chat_previous"
    assert _descriptions(previous_chat) == ["press_keys: ctrl+shift+tab"]
    assert next_chat is not None
    assert next_chat.action_name == "chat_next"
    assert _descriptions(next_chat) == ["press_keys: ctrl+tab"]


def test_runtime_right_stick_x_emits_focus_target_dry_run_output():
    runtime = _runtime()

    chat_list = runtime.update_axis("right_stick_x", -0.8, now=0.0)
    runtime.update_axis("right_stick_x", 0.0, now=0.1)
    message_pane = runtime.update_axis("right_stick_x", 0.8, now=0.3)

    assert chat_list is not None
    assert chat_list.action_name == "focus_chat_list"
    assert _descriptions(chat_list) == ["focus_mouse_target: chat_list click=False"]
    assert message_pane is not None
    assert message_pane.action_name == "focus_message_pane"
    assert _descriptions(message_pane) == ["focus_mouse_target: message_pane click=True"]


def test_runtime_right_stick_y_emits_scroll_dry_run_output():
    cases = [
        (-0.8, "scroll_up", ["scroll: 0.25"]),
        (0.8, "scroll_down", ["scroll: -0.25"]),
    ]

    for value, action_name, expected_output in cases:
        result = _runtime().update_axis("right_stick_y", value, now=0.0)

        assert result is not None
        assert result.action_name == action_name
        assert _descriptions(result) == expected_output


def test_runtime_dpad_emits_cursor_movement_dry_run_output():
    cases = [
        ((0, 1), "cursor_up", ["press_keys: up"]),
        ((0, -1), "cursor_down", ["press_keys: down"]),
        ((-1, 0), "cursor_left", ["press_keys: left"]),
        ((1, 0), "cursor_right", ["press_keys: right"]),
    ]

    for value, action_name, expected_output in cases:
        result = _runtime().update_hat("dpad", value, now=0.0)

        assert result is not None
        assert result.action_name == action_name
        assert _descriptions(result) == expected_output
