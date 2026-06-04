import json
from pathlib import Path

import pytest

from ai_operator_controller.learning import (
    LearningCandidateValidationError,
    load_learning_candidate_file,
    validate_learning_candidate_file,
)


EXAMPLE_PATH = Path("config/examples/learning-candidates.example.json")


def test_public_learning_candidates_example_loads_and_validates():
    candidate_file = load_learning_candidate_file(EXAMPLE_PATH)

    assert candidate_file.schema_version == 1
    assert {candidate.candidate_type for candidate in candidate_file.candidates} == {
        "assistant_guard",
        "hotword",
        "punctuation_hint",
        "replacement",
    }
    assert all(candidate.status == "candidate" for candidate in candidate_file.candidates)


def test_learning_candidate_validation_rejects_raw_private_content_fields():
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    data["candidates"][0]["raw_text"] = "verbatim private chat message"

    with pytest.raises(LearningCandidateValidationError, match="raw_text"):
        validate_learning_candidate_file(data, source=EXAMPLE_PATH)


def test_learning_candidate_validation_rejects_unknown_candidate_type():
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    data["candidates"][0]["candidate_type"] = "copy_full_chat_history"

    with pytest.raises(LearningCandidateValidationError, match="candidate_type"):
        validate_learning_candidate_file(data, source=EXAMPLE_PATH)
