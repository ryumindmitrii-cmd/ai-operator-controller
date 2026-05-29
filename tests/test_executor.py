import pytest

from ai_operator_controller.executor import (
    ActionExecutor,
    DryRunOutputBackend,
    OutputEvent,
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

    assert backend.events == [OutputEvent(kind="scroll", scroll_clicks=-2)]


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
