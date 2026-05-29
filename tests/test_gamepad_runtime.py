from pathlib import Path

from ai_operator_controller.config import load_profile
from ai_operator_controller.gamepad import (
    GamepadActionRuntime,
    bindings_from_profile,
)


PROFILE_PATH = Path("config/examples/profile.codex.windows.json")


def test_profile_builds_gamepad_bindings():
    bindings = bindings_from_profile(load_profile(PROFILE_PATH))

    assert sorted(bindings.buttons) == ["a", "b", "lb", "rb", "x"]
    assert sorted(bindings.axes) == [
        "left_stick_y",
        "lt",
        "right_stick_x",
        "right_stick_y",
        "rt",
    ]
    assert sorted(bindings.hats) == ["dpad"]
    assert bindings.buttons["b"].repeat is True


def test_runtime_axis_emits_action_and_dry_run_output():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    result = runtime.update_axis("right_stick_x", 0.8, now=0.0)

    assert result is not None
    assert result.action_name == "focus_message_pane"
    assert [event.describe() for event in result.output_events] == [
        "focus_mouse_target: message_pane click=True"
    ]


def test_runtime_axis_emits_scroll_action_and_dry_run_output():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    result = runtime.update_axis("right_stick_y", 0.8, now=0.0)

    assert result is not None
    assert result.action_name == "scroll_down"
    assert [event.describe() for event in result.output_events] == ["scroll: -0.25"]


def test_runtime_hat_emits_cursor_action_and_dry_run_output():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    result = runtime.update_hat("dpad", (1, 0), now=0.0)

    assert result is not None
    assert result.action_name == "cursor_right"
    assert [event.describe() for event in result.output_events] == ["press_keys: right"]


def test_runtime_button_repeats_when_held_after_cooldown():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    first = runtime.update_button("b", True, now=0.0)
    blocked = runtime.update_button("b", True, now=0.05)
    repeated = runtime.update_button("b", True, now=0.1)

    assert first is not None
    assert first.action_name == "backspace"
    assert [event.describe() for event in first.output_events] == ["press_keys: backspace"]
    assert blocked is None
    assert repeated is not None
    assert repeated.action_name == "backspace"


def test_runtime_bumper_buttons_emit_mouse_clicks():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    left = runtime.update_button("lb", True, now=0.0)
    right = runtime.update_button("rb", True, now=0.0)

    assert left is not None
    assert left.action_name == "mouse_left_click"
    assert [event.describe() for event in left.output_events] == ["click_mouse: left"]
    assert right is not None
    assert right.action_name == "mouse_right_click"
    assert [event.describe() for event in right.output_events] == ["click_mouse: right"]


def test_runtime_reports_future_dictation_action_without_output_effect():
    runtime = GamepadActionRuntime(bindings_from_profile(load_profile(PROFILE_PATH)))

    result = runtime.update_button("a", True, now=0.0)

    assert result is not None
    assert result.action_name == "dictate_paste"
    assert result.output_events == ()
    assert result.unsupported_reason == "Action has no keyboard plan: dictate_paste"
