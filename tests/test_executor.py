import pytest

from ai_operator_controller.executor import (
    ActionExecutor,
    DryRunOutputBackend,
    OutputEvent,
    RecordingOutputBackend,
)


def test_executor_sends_key_actions_to_backend():
    backend = DryRunOutputBackend()
    executor = ActionExecutor(backend)

    executor.execute("cursor_left")

    assert backend.events == [OutputEvent(kind="press_keys", keys=("left",))]


def test_executor_sends_scroll_actions_to_backend():
    backend = DryRunOutputBackend()
    executor = ActionExecutor(backend)

    executor.execute("scroll_down")

    assert backend.events == [OutputEvent(kind="scroll", scroll_clicks=-0.25)]


def test_executor_sends_focus_actions_to_backend():
    backend = DryRunOutputBackend()
    executor = ActionExecutor(backend)

    executor.execute("focus_message_pane")

    assert backend.events == [
        OutputEvent(kind="focus_mouse_target", mouse_target="message_pane", click=True)
    ]


def test_executor_sends_mouse_click_actions_to_backend():
    backend = DryRunOutputBackend()
    executor = ActionExecutor(backend)

    executor.execute("mouse_right_click")

    assert backend.events == [OutputEvent(kind="click_mouse", mouse_button="right")]


def test_executor_rejects_actions_without_output_plan():
    backend = DryRunOutputBackend()
    executor = ActionExecutor(backend)

    with pytest.raises(ValueError, match="Action has no keyboard plan"):
        executor.execute("dictate_paste")


def test_recording_backend_delegates_without_storing_text():
    class SpyBackend:
        def __init__(self):
            self.calls = []

        def press_keys(self, keys):
            self.calls.append(("press_keys", keys))

        def scroll(self, clicks):
            self.calls.append(("scroll", clicks))

        def focus_mouse_target(self, target, *, click):
            self.calls.append(("focus_mouse_target", target, click))

        def click_mouse(self, button):
            self.calls.append(("click_mouse", button))

        def write_text(self, text, *, target):
            self.calls.append(("write_text", text, target))

    spy = SpyBackend()
    backend = RecordingOutputBackend(spy)

    backend.write_text("private dictated text", target="paste")
    backend.press_keys(("enter",))

    assert spy.calls == [
        ("write_text", "private dictated text", "paste"),
        ("press_keys", ("enter",)),
    ]
    assert backend.events == [
        OutputEvent(kind="write_text", text_target="paste", text_length=21),
        OutputEvent(kind="press_keys", keys=("enter",)),
    ]
