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


def test_run_dictation_once_blocks_auto_send_when_confidence_is_low():
    rules = TextRules(send_commands=["send"])

    result = run_dictation_once(
        "dictate_paste",
        StaticTranscriptProvider("please check this send"),
        rules=rules,
        transcription_confidence=0.2,
    )

    assert result.should_send is True
    assert result.quality.confidence == "low"
    assert result.quality.send_allowed is False
    assert result.quality.review_required is True
    assert result.output_events == (
        OutputEvent(kind="write_text", text_target="paste", text_length=17),
    )


def test_run_dictation_once_blocks_auto_send_for_long_text():
    rules = TextRules(send_commands=["send"])
    long_text = " ".join(["word"] * 40)

    result = run_dictation_once(
        "dictate_paste",
        StaticTranscriptProvider(f"{long_text} send"),
        rules=rules,
        review_long_text_chars=100,
    )

    assert result.should_send is True
    assert result.quality.confidence == "medium"
    assert result.quality.send_allowed is False
    assert result.quality.review_required is True
    assert result.output_events == (
        OutputEvent(kind="write_text", text_target="paste", text_length=len(long_text)),
    )


def test_run_dictation_once_rejects_non_dictation_actions():
    with pytest.raises(ValueError, match="dictation action"):
        run_dictation_once("cursor_left", StaticTranscriptProvider("hello"))
