from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Literal


LearningCandidateType = Literal[
    "assistant_guard",
    "domain_term",
    "hotword",
    "punctuation_hint",
    "replacement",
]
LearningCandidateStatus = Literal["candidate", "approved", "rejected"]

ALLOWED_CANDIDATE_TYPES = frozenset(
    {
        "assistant_guard",
        "domain_term",
        "hotword",
        "punctuation_hint",
        "replacement",
    }
)
ALLOWED_STATUSES = frozenset({"candidate", "approved", "rejected"})
FORBIDDEN_CONTENT_KEYS = frozenset(
    {
        "audio_path",
        "clipboard",
        "message_body",
        "raw_chat",
        "raw_text",
        "recording",
        "source_excerpt",
        "transcript",
    }
)


class LearningCandidateValidationError(ValueError):
    pass


@dataclass(frozen=True)
class LearningCandidate:
    candidate_id: str
    project_profile: str
    candidate_type: LearningCandidateType
    status: LearningCandidateStatus
    source_ref: str
    payload: Mapping[str, Any]
    reason: str


@dataclass(frozen=True)
class LearningCandidateFile:
    schema_version: int
    candidates: tuple[LearningCandidate, ...]


def load_learning_candidate_file(path: str | Path) -> LearningCandidateFile:
    candidate_path = Path(path)
    try:
        data = json.loads(candidate_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LearningCandidateValidationError(f"{candidate_path}: cannot read file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LearningCandidateValidationError(f"{candidate_path}: invalid JSON: {exc}") from exc
    return validate_learning_candidate_file(data, source=candidate_path)


def validate_learning_candidate_file(
    data: Mapping[str, Any],
    *,
    source: str | Path | None = None,
) -> LearningCandidateFile:
    label = str(source) if source is not None else "learning candidate file"
    if not isinstance(data, Mapping):
        raise LearningCandidateValidationError(f"{label}: file must be a JSON object")
    _reject_forbidden_content_keys(data, label)

    schema_version = _require_int(data, "schema_version", label)
    if schema_version != 1:
        raise LearningCandidateValidationError(f"{label}: schema_version must be 1")

    raw_candidates = _require_list(data, "candidates", label)
    candidates = tuple(
        _validate_candidate(item, f"{label}: candidates[{index}]")
        for index, item in enumerate(raw_candidates)
    )
    return LearningCandidateFile(schema_version=schema_version, candidates=candidates)


def _validate_candidate(value: Any, label: str) -> LearningCandidate:
    if not isinstance(value, Mapping):
        raise LearningCandidateValidationError(f"{label}: candidate must be an object")
    _reject_forbidden_content_keys(value, label)

    candidate_type = _require_str(value, "candidate_type", label)
    if candidate_type not in ALLOWED_CANDIDATE_TYPES:
        raise LearningCandidateValidationError(f"{label}: unknown candidate_type: {candidate_type}")

    status = _require_str(value, "status", label)
    if status not in ALLOWED_STATUSES:
        raise LearningCandidateValidationError(f"{label}: unknown status: {status}")

    payload = _require_mapping(value, "payload", label)
    _reject_forbidden_content_keys(payload, f"{label}: payload")

    return LearningCandidate(
        candidate_id=_require_str(value, "id", label),
        project_profile=_require_str(value, "project_profile", label),
        candidate_type=candidate_type,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        source_ref=_require_str(value, "source_ref", label),
        payload=payload,
        reason=_require_str(value, "reason", label),
    )


def _reject_forbidden_content_keys(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            if isinstance(key, str) and key in FORBIDDEN_CONTENT_KEYS:
                raise LearningCandidateValidationError(
                    f"{label}: forbidden raw private content field: {key}"
                )
            _reject_forbidden_content_keys(nested_value, label)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden_content_keys(item, label)


def _require_str(mapping: Mapping[str, Any], key: str, label: str) -> str:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise LearningCandidateValidationError(f"{label}: missing required string: {key}") from exc
    if not isinstance(value, str) or not value:
        raise LearningCandidateValidationError(f"{label}: {key} must be a non-empty string")
    return value


def _require_int(mapping: Mapping[str, Any], key: str, label: str) -> int:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise LearningCandidateValidationError(f"{label}: missing required integer: {key}") from exc
    if isinstance(value, bool) or not isinstance(value, int):
        raise LearningCandidateValidationError(f"{label}: {key} must be an integer")
    return value


def _require_list(mapping: Mapping[str, Any], key: str, label: str) -> list[Any]:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise LearningCandidateValidationError(f"{label}: missing required list: {key}") from exc
    if not isinstance(value, list):
        raise LearningCandidateValidationError(f"{label}: {key} must be a list")
    return value


def _require_mapping(mapping: Mapping[str, Any], key: str, label: str) -> Mapping[str, Any]:
    try:
        value = mapping[key]
    except KeyError as exc:
        raise LearningCandidateValidationError(f"{label}: missing required object: {key}") from exc
    if not isinstance(value, Mapping):
        raise LearningCandidateValidationError(f"{label}: {key} must be an object")
    return value
