from pathlib import Path

from ai_operator_controller.text_rules import TextRules, clean_dictation, load_text_rules


def test_clean_dictation_applies_replacements_and_removes_trash_phrases():
    rules = TextRules(
        replace_phrases={"new line": "\n", "colon": ":", "semicolon": ";"},
        trash_phrases=["um", "you know"],
    )

    result = clean_dictation("Um label colon value semicolon new line you know next line", rules)

    assert result.text == "label: value;\nnext line"
    assert result.should_send is False


def test_clean_dictation_detects_and_removes_trailing_send_command():
    rules = TextRules(send_commands=["send", "send message"])

    result = clean_dictation("please summarize this send message", rules)

    assert result.text == "please summarize this"
    assert result.should_send is True


def test_load_text_rules_reads_public_example_config():
    rules = load_text_rules(Path("config/examples/replacements.example.json"))

    result = clean_dictation("uh first line new line second line send", rules)

    assert result.text == "first line\nsecond line"
    assert result.should_send is True
