from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Any


@dataclass(frozen=True)
class TextRules:
    replace_phrases: Mapping[str, str] = field(default_factory=dict)
    trash_phrases: Sequence[str] = field(default_factory=tuple)
    send_commands: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class CleanedDictation:
    text: str
    should_send: bool = False


def load_text_rules(path: str | Path) -> TextRules:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return TextRules(
        replace_phrases=_dict_of_strings(data.get("replace_phrases", {}), "replace_phrases"),
        trash_phrases=_list_of_strings(data.get("trash_phrases", []), "trash_phrases"),
        send_commands=_list_of_strings(data.get("send_commands", []), "send_commands"),
    )


def clean_dictation(text: str, rules: TextRules | None = None) -> CleanedDictation:
    rules = rules or TextRules()
    cleaned = _collapse_whitespace(text)
    cleaned, should_send = _strip_trailing_send_command(cleaned, rules.send_commands)
    cleaned = _remove_phrases(cleaned, rules.trash_phrases)
    cleaned = _replace_phrases(cleaned, rules.replace_phrases)
    return CleanedDictation(text=_tidy_text(cleaned), should_send=should_send)


def _dict_of_strings(value: Any, field_name: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")

    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only string keys and values")
        result[key] = item
    return result


def _list_of_strings(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must contain only strings")
    return value


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_trailing_send_command(text: str, send_commands: Sequence[str]) -> tuple[str, bool]:
    for command in sorted(send_commands, key=len, reverse=True):
        command = command.strip()
        if not command:
            continue

        pattern = re.compile(rf"(?:^|\s){re.escape(command)}$", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return text[: match.start()].strip(), True

    return text, False


def _remove_phrases(text: str, phrases: Sequence[str]) -> str:
    result = text
    for phrase in sorted(phrases, key=len, reverse=True):
        phrase = phrase.strip()
        if not phrase:
            continue
        result = _phrase_pattern(phrase).sub(" ", result)
    return _collapse_whitespace(result)


def _replace_phrases(text: str, replacements: Mapping[str, str]) -> str:
    result = text
    for phrase, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        phrase = phrase.strip()
        if not phrase:
            continue
        result = _phrase_pattern(phrase).sub(replacement, result)
    return result


def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE)


def _tidy_text(text: str) -> str:
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
