from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
    output_events: tuple[OutputEvent, ...]


def run_dictation_once(
    action_name: str,
    transcript_provider: TranscriptProvider,
    *,
    rules: TextRules | None = None,
    polish: bool = False,
) -> DictationRunResult:
    try:
        output_target = DICTATION_ACTION_TARGETS[action_name]
    except KeyError as exc:
        raise ValueError(f"Expected dictation action, got: {action_name}") from exc

    cleaned = clean_dictation(transcript_provider.transcribe_once(), rules)
    output_text = polish_text(cleaned.text) if polish else cleaned.text
    backend = DryRunOutputBackend()
    backend.write_text(output_text, target=output_target)

    if output_target == "paste" and cleaned.should_send:
        ActionExecutor(backend).execute("enter")

    return DictationRunResult(
        action_name=action_name,
        output_target=output_target,
        text=output_text,
        should_send=cleaned.should_send,
        output_events=tuple(backend.events),
    )
