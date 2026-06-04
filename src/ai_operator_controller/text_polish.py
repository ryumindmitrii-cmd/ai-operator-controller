from __future__ import annotations

import re


_INTRO_MARKERS = (
    "так",
    "смотри",
    "слушай",
    "короче",
    "значит",
    "в общем",
)


def polish_text(text: str) -> str:
    """Apply conservative local punctuation polish to dictated text.

    This function is intentionally deterministic and local-only. It may adjust
    punctuation, spacing, and sentence capitalization, but it must not add new
    content or depend on an external language model.
    """

    normalized = _normalize_spacing(text)
    lines = [_polish_line(line) for line in normalized.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _polish_line(line: str) -> str:
    line = _normalize_inline_spacing(line)
    if not line:
        return ""

    line = _add_intro_commas(line)
    line = _add_clause_commas(line)
    line = _normalize_inline_spacing(line)
    line = _ensure_terminal_punctuation(line)
    line = _capitalize_sentences(line)
    return line


def _normalize_spacing(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    return "\n".join(_normalize_inline_spacing(line) for line in text.splitlines()).strip()


def _normalize_inline_spacing(text: str) -> str:
    text = re.sub(r"\s+([,.;:!?])", r"\1", text.strip())
    text = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _add_intro_commas(text: str) -> str:
    result = text
    for _ in range(2):
        for marker in sorted(_INTRO_MARKERS, key=len, reverse=True):
            pattern = re.compile(
                rf"(^|[,.!?]\s+)({re.escape(marker)})(\s+)(?![,.;:!?])",
                re.IGNORECASE,
            )
            result = pattern.sub(r"\1\2, ", result)
    return result


def _add_clause_commas(text: str) -> str:
    result = text
    result = re.sub(r"(?<![,.;:!?])\s+\bно\b", ", но", result, flags=re.IGNORECASE)
    result = re.sub(r"(?<!потому)(?<![,.;:!?])\s+\bчто\b", ", что", result, flags=re.IGNORECASE)
    return result


def _ensure_terminal_punctuation(text: str) -> str:
    if not text:
        return text
    if text[-1] in ".!?…":
        return text
    if text[-1] in ",;:":
        return f"{text[:-1]}."
    return f"{text}."


def _capitalize_sentences(text: str) -> str:
    chars: list[str] = []
    should_capitalize = True

    for char in text:
        if should_capitalize and char.isalpha():
            chars.append(char.upper())
            should_capitalize = False
            continue

        chars.append(char)
        if char in ".!?…":
            should_capitalize = True

    return "".join(chars)
