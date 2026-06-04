from ai_operator_controller.text_polish import polish_text


def test_polish_text_adds_common_russian_dictation_punctuation():
    result = polish_text(
        "так смотри я думаю что это можно сделать но надо сначала проверить локально"
    )

    assert result == "Так, смотри, я думаю, что это можно сделать, но надо сначала проверить локально."


def test_polish_text_preserves_existing_punctuation_and_spacing():
    result = polish_text("  привет ,  это Codex  .  дальше проверяем  ")

    assert result == "Привет, это Codex. Дальше проверяем."


def test_polish_text_handles_multiline_text_independently():
    result = polish_text("первый пункт\nтак смотри второй пункт")

    assert result == "Первый пункт.\nТак, смотри, второй пункт."
