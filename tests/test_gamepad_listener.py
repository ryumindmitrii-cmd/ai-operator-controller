from pathlib import Path
import sys

import pytest

from ai_operator_controller.config import load_profile
from ai_operator_controller.gamepad import GamepadActionRuntime, bindings_from_profile
from ai_operator_controller.gamepad_listener import (
    GamepadState,
    PygameGamepadReader,
    _detect_joystick_count,
    listen_gamepad_dry_run,
    poll_gamepad_state,
)


PROFILE_PATH = Path("config/examples/profile.codex.windows.json")


def _runtime_and_bindings():
    bindings = bindings_from_profile(load_profile(PROFILE_PATH))
    return GamepadActionRuntime(bindings), bindings


def test_poll_gamepad_state_emits_button_action():
    runtime, bindings = _runtime_and_bindings()

    actions = poll_gamepad_state(
        runtime,
        bindings,
        GamepadState(buttons={1: True}, axes={}, hats={}),
        now=0.0,
    )

    assert len(actions) == 1
    assert actions[0].input_kind == "button"
    assert actions[0].input_name == "b"
    assert actions[0].raw_index == 1
    assert actions[0].raw_value == "down"
    assert actions[0].result.action_name == "backspace"
    assert [event.describe() for event in actions[0].result.output_events] == [
        "press_keys: backspace"
    ]


def test_poll_gamepad_state_repeats_held_button_after_cooldown():
    runtime, bindings = _runtime_and_bindings()
    state = GamepadState(buttons={1: True}, axes={}, hats={})

    first = poll_gamepad_state(runtime, bindings, state, now=0.0)
    blocked = poll_gamepad_state(runtime, bindings, state, now=0.05)
    repeated = poll_gamepad_state(runtime, bindings, state, now=0.1)

    assert [action.result.action_name for action in first] == ["backspace"]
    assert blocked == []
    assert [action.result.action_name for action in repeated] == ["backspace"]


def test_poll_gamepad_state_emits_axis_action():
    runtime, bindings = _runtime_and_bindings()

    actions = poll_gamepad_state(
        runtime,
        bindings,
        GamepadState(buttons={}, axes={2: 0.8}, hats={}),
        now=0.0,
    )

    assert len(actions) == 1
    assert actions[0].input_kind == "axis"
    assert actions[0].input_name == "right_stick_x"
    assert actions[0].raw_index == 2
    assert actions[0].raw_value == "0.800"
    assert actions[0].result.action_name == "focus_message_pane"


def test_poll_gamepad_state_emits_hat_action():
    runtime, bindings = _runtime_and_bindings()

    actions = poll_gamepad_state(
        runtime,
        bindings,
        GamepadState(buttons={}, axes={}, hats={0: (0, -1)}),
        now=0.0,
    )

    assert len(actions) == 1
    assert actions[0].input_kind == "hat"
    assert actions[0].input_name == "dpad"
    assert actions[0].raw_index == 0
    assert actions[0].raw_value == "0 -1"
    assert actions[0].result.action_name == "cursor_down"


def test_listen_gamepad_dry_run_emits_until_max_events():
    _, bindings = _runtime_and_bindings()
    reader = FakeReader(
        [
            GamepadState(buttons={1: False}, axes={}, hats={}),
            GamepadState(buttons={1: True}, axes={}, hats={}),
        ]
    )
    emitted = []

    count = listen_gamepad_dry_run(
        bindings,
        reader,
        max_events=1,
        poll_interval_seconds=0.01,
        clock=FakeClock([0.0, 0.1]),
        sleep=lambda _seconds: None,
        emit=emitted.append,
    )

    assert count == 1
    assert reader.closed is True
    assert [action.result.action_name for action in emitted] == ["backspace"]


def test_pygame_reader_reports_missing_dependency(monkeypatch):
    monkeypatch.setitem(sys.modules, "pygame", None)

    with pytest.raises(RuntimeError, match="pygame is required"):
        PygameGamepadReader()


def test_detect_joystick_count_reinitializes_after_empty_scan(monkeypatch):
    monkeypatch.setattr("ai_operator_controller.gamepad_listener.time.sleep", lambda _seconds: None)
    fake_pygame = FakePygame([0, 1])

    count = _detect_joystick_count(fake_pygame, attempts=2)

    assert count == 1
    assert fake_pygame.quit_calls == 1
    assert fake_pygame.joystick.quit_calls == 2
    assert fake_pygame.joystick.init_calls == 2


class FakeReader:
    controller_name = "Fake Controller"

    def __init__(self, states):
        self._states = list(states)
        self.closed = False

    def read_state(self):
        if len(self._states) == 1:
            return self._states[0]
        return self._states.pop(0)

    def close(self):
        self.closed = True


class FakeClock:
    def __init__(self, values):
        self._values = list(values)

    def __call__(self):
        if len(self._values) == 1:
            return self._values[0]
        return self._values.pop(0)


class FakePygame:
    def __init__(self, counts):
        self.joystick = FakeJoystickModule(counts)
        self.event = FakeEventModule()
        self.quit_calls = 0

    def init(self):
        pass

    def quit(self):
        self.quit_calls += 1


class FakeJoystickModule:
    def __init__(self, counts):
        self._counts = list(counts)
        self.init_calls = 0
        self.quit_calls = 0

    def init(self):
        self.init_calls += 1

    def quit(self):
        self.quit_calls += 1

    def get_count(self):
        if len(self._counts) == 1:
            return self._counts[0]
        return self._counts.pop(0)


class FakeEventModule:
    def pump(self):
        pass
