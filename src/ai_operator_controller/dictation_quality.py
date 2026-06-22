from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Literal


DictationConfidence = Literal["high", "medium", "low"]
OutputTarget = Literal["paste", "clipboard"]


@dataclass(frozen=True)
class DictationQualityReport:
    raw_text: str
    clean_text: str
    final_text: str
    requested_send: bool
    output_target: OutputTarget
    transcription_confidence: float | None
    postprocess_changed: bool
    postprocess_change_ratio: float
    confidence: DictationConfidence
    review_required: bool
    output_allowed: bool
    send_allowed: bool
    reasons: tuple[str, ...]


def assess_dictation_quality(
    *,
    raw_text: str,
    clean_text: str,
    final_text: str,
    requested_send: bool,
    output_target: OutputTarget,
    transcription_confidence: float | None = None,
    review_long_text_chars: int = 240,
    max_postprocess_change_ratio: float = 0.25,
    min_transcription_confidence: float = 0.55,
    medium_transcription_confidence: float = 0.75,
    blocked_output_phrases: Sequence[str] = (),
    low_input_signal: bool = False,
) -> DictationQualityReport:
    """Assess whether dictation output is safe to auto-send.

    The report is deterministic and local-only. It is intentionally conservative
    because false confidence is worse than leaving text in the input box.
    """

    _validate_quality_options(
        output_target=output_target,
        transcription_confidence=transcription_confidence,
        review_long_text_chars=review_long_text_chars,
        max_postprocess_change_ratio=max_postprocess_change_ratio,
        min_transcription_confidence=min_transcription_confidence,
        medium_transcription_confidence=medium_transcription_confidence,
        blocked_output_phrases=blocked_output_phrases,
        low_input_signal=low_input_signal,
    )

    change_ratio = _text_change_ratio(clean_text, final_text)
    postprocess_changed = _normalize_text(clean_text) != _normalize_text(final_text)
    reasons: list[str] = []
    has_low_signal = False
    has_medium_signal = False
    output_blocked = False

    if not final_text.strip():
        reasons.append("empty_text")
        has_low_signal = True
        output_blocked = True

    if low_input_signal:
        reasons.append("low_input_signal")
        has_low_signal = True
        output_blocked = True

    if _matches_blocked_phrase(final_text, blocked_output_phrases):
        reasons.append("blocked_transcript_phrase")
        has_low_signal = True
        output_blocked = True

    if transcription_confidence is not None:
        if transcription_confidence < min_transcription_confidence:
            reasons.append("low_transcription_confidence")
            has_low_signal = True
        elif transcription_confidence < medium_transcription_confidence:
            reasons.append("medium_transcription_confidence")
            has_medium_signal = True

    if len(final_text) > review_long_text_chars:
        reasons.append("long_text")
        has_medium_signal = True

    if change_ratio > max_postprocess_change_ratio:
        reasons.append("large_postprocess_change")
        has_medium_signal = True

    if has_low_signal:
        confidence: DictationConfidence = "low"
    elif has_medium_signal:
        confidence = "medium"
    else:
        confidence = "high"

    auto_send_requested = requested_send and output_target == "paste"
    output_allowed = bool(final_text.strip()) and not output_blocked
    review_required = auto_send_requested and (confidence != "high" or not output_allowed)
    send_allowed = auto_send_requested and output_allowed and not review_required

    return DictationQualityReport(
        raw_text=raw_text,
        clean_text=clean_text,
        final_text=final_text,
        requested_send=requested_send,
        output_target=output_target,
        transcription_confidence=transcription_confidence,
        postprocess_changed=postprocess_changed,
        postprocess_change_ratio=change_ratio,
        confidence=confidence,
        review_required=review_required,
        output_allowed=output_allowed,
        send_allowed=send_allowed,
        reasons=tuple(reasons),
    )


def _validate_quality_options(
    *,
    output_target: str,
    transcription_confidence: float | None,
    review_long_text_chars: int,
    max_postprocess_change_ratio: float,
    min_transcription_confidence: float,
    medium_transcription_confidence: float,
    blocked_output_phrases: Sequence[str],
    low_input_signal: bool,
) -> None:
    if output_target not in {"paste", "clipboard"}:
        raise ValueError(f"unknown dictation output target: {output_target}")
    if transcription_confidence is not None and not 0 <= transcription_confidence <= 1:
        raise ValueError("transcription_confidence must be between 0 and 1")
    if review_long_text_chars < 0:
        raise ValueError("review_long_text_chars must be non-negative")
    if not 0 <= max_postprocess_change_ratio <= 1:
        raise ValueError("max_postprocess_change_ratio must be between 0 and 1")
    if not 0 <= min_transcription_confidence <= 1:
        raise ValueError("min_transcription_confidence must be between 0 and 1")
    if not 0 <= medium_transcription_confidence <= 1:
        raise ValueError("medium_transcription_confidence must be between 0 and 1")
    if min_transcription_confidence > medium_transcription_confidence:
        raise ValueError("min_transcription_confidence cannot exceed medium_transcription_confidence")
    if isinstance(blocked_output_phrases, str) or not all(
        isinstance(phrase, str) for phrase in blocked_output_phrases
    ):
        raise ValueError("blocked_output_phrases must be a sequence of strings")
    if not isinstance(low_input_signal, bool):
        raise ValueError("low_input_signal must be a boolean")


def _text_change_ratio(before: str, after: str) -> float:
    normalized_before = _normalize_text(before)
    normalized_after = _normalize_text(after)
    if normalized_before == normalized_after:
        return 0.0
    if not normalized_before and normalized_after:
        return 1.0
    if normalized_before and not normalized_after:
        return 1.0
    return 1 - SequenceMatcher(None, normalized_before, normalized_after).ratio()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _matches_blocked_phrase(text: str, blocked_phrases: Sequence[str]) -> bool:
    normalized_text = _normalize_blocked_phrase(text)
    if len(normalized_text) < 8:
        return False

    for phrase in blocked_phrases:
        normalized_phrase = _normalize_blocked_phrase(phrase)
        if len(normalized_phrase) < 8:
            continue
        if normalized_text == normalized_phrase:
            return True
        if normalized_text in normalized_phrase:
            return True
        if normalized_phrase in normalized_text:
            return True
        if SequenceMatcher(None, normalized_text, normalized_phrase).ratio() >= 0.92:
            return True
    return False


def _normalize_blocked_phrase(text: str) -> str:
    return _normalize_text(re.sub(r"[^\w]+", " ", text.casefold()))
