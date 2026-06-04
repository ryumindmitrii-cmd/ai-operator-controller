from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .dictation_quality import DictationQualityReport, assess_dictation_quality
from .executor import ActionExecutor, DryRunOutputBackend, OutputEvent, TextOutputTarget
from .text_polish import polish_text
from .text_rules import TextRules, clean_dictation


DICTATION_ACTION_TARGETS: dict[str, TextOutputTarget] = {
    "dictate_paste": "paste",
    "dictate_clipboard": "clipboard",
}


class TranscriptProvider(Protocol):
    def transcribe_once(self) -> str:
        pass


@dataclass(frozen=True)
class StaticTranscriptProvider:
    text: str

    def transcribe_once(self) -> str:
        return self.text


@dataclass(frozen=True)
class DictationRunResult:
    action_name: str
    output_target: TextOutputTarget
    text: str
    should_send: bool
    quality: DictationQualityReport
    output_events: tuple[OutputEvent, ...]


def run_dictation_once(
    action_name: str,
    transcript_provider: TranscriptProvider,
    *,
    rules: TextRules | None = None,
    polish: bool = False,
    transcription_confidence: float | None = None,
    review_long_text_chars: int = 240,
    max_postprocess_change_ratio: float = 0.25,
) -> DictationRunResult:
    try:
        output_target = DICTATION_ACTION_TARGETS[action_name]
    except KeyError as exc:
        raise ValueError(f"Expected dictation action, got: {action_name}") from exc

    raw_text = transcript_provider.transcribe_once()
    cleaned = clean_dictation(raw_text, rules)
    output_text = polish_text(cleaned.text) if polish else cleaned.text
    quality = assess_dictation_quality(
        raw_text=raw_text,
        clean_text=cleaned.text,
        final_text=output_text,
        requested_send=cleaned.should_send,
        output_target=output_target,
        transcription_confidence=transcription_confidence,
        review_long_text_chars=review_long_text_chars,
        max_postprocess_change_ratio=max_postprocess_change_ratio,
    )
    backend = DryRunOutputBackend()
    backend.write_text(output_text, target=output_target)

    if quality.send_allowed:
        ActionExecutor(backend).execute("enter")

    return DictationRunResult(
        action_name=action_name,
        output_target=output_target,
        text=output_text,
        should_send=cleaned.should_send,
        quality=quality,
        output_events=tuple(backend.events),
    )
