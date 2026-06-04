import pytest

from ai_operator_controller.executor import OutputEvent
from ai_operator_controller.runtime import (
    StaticTranscriptProvider,
    run_dictation_once,
)
from ai_operator_controller.text_rules import TextRules


def test_run_dictation_once_cleans_text_and_plans_paste_output():
    rules = TextRules(
        replace_phrases={"new line": "\n"},
        trash_phrases=["um"],
        send_commands=["send"],
    )

    result = run_dictation_once(
        "dictate_paste",
        StaticTranscriptProvider("um first line new line second line send"),
        rules=rules,
    )

    assert result.action_name == "dictate_paste"
    assert result.output_target == "paste"
    assert result.text == "first line\nsecond line"
    assert result.should_send is True
    assert result.output_events == (
        OutputEvent(kind="write_text", text_target="paste", text_length=22),
        OutputEvent(kind="press_keys", keys=("enter",)),
    )


def test_run_dictation_once_can_polish_cleaned_text():
    result = run_dictation_once(
        "dictate_paste",
        StaticTranscriptProvider("так смотри я думаю что это можно сделать"),
        polish=True,
    )

    assert result.text == "Так, смотри, я думаю, что это можно сделать."


def test_run_dictation_once_clipboard_mode_does_not_plan_enter():
    rules = TextRules(send_commands=["send"])

    result = run_dictation_once(
        "dictate_clipboard",
        StaticTranscriptProvider("draft only send"),
        rules=rules,
    )

    assert result.output_target == "clipboard"
    assert result.text == "draft only"
    assert result.should_send is True
    assert result.output_events == (
        OutputEvent(kind="write_text", text_target="clipboard", text_length=10),
    )


def test_run_dictation_once_rejects_non_dictation_actions():
    with pytest.raises(ValueError, match="dictation action"):
        run_dictation_once("cursor_left", StaticTranscriptProvider("hello"))
