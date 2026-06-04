import json
from pathlib import Path

import pytest

from ai_operator_controller.config import (
    ProfileValidationError,
    load_profile,
    validate_profile,
)


PROFILE_PATH = Path("config/examples/profile.codex.windows.json")
SPEECH_PROFILE_PATH = Path("config/examples/speech.local-quality.example.json")


def test_public_codex_profile_loads_and_validates():
    profile = load_profile(PROFILE_PATH)

    result = validate_profile(profile, source=PROFILE_PATH)

    assert result.profile_name == "codex_windows_default"
    assert "dictate_paste" in result.actions
    assert "cursor_left" in result.actions
    assert result.button_count == 5
    assert result.axis_count == 5
    assert result.hat_count == 1


def test_profile_validation_rejects_unknown_actions():
    profile = json.loads(PROFILE_PATH.read_text())
    profile["gamepad"]["buttons"]["a"]["action"] = "open_private_file"

    with pytest.raises(ProfileValidationError, match="Unknown action"):
        validate_profile(profile, source=PROFILE_PATH)


def test_profile_validation_rejects_invalid_focus_target():
    profile = json.loads(PROFILE_PATH.read_text())
    profile["gamepad"]["buttons"]["a"]["focus_before_action"]["x_ratio"] = 1.5

    with pytest.raises(ProfileValidationError, match="x_ratio"):
        validate_profile(profile, source=PROFILE_PATH)


def test_profile_validation_rejects_private_path_markers():
    profile = json.loads(PROFILE_PATH.read_text())
    profile["description"] = r"Synthetic private path at X:\private-prototype"

    with pytest.raises(ProfileValidationError, match="private/local marker"):
        validate_profile(profile, source=PROFILE_PATH)


def test_public_speech_profile_uses_quality_model_by_default():
    profile = json.loads(SPEECH_PROFILE_PATH.read_text())

    assert profile["backend"] == "faster-whisper"
    assert profile["model"] == "large-v3"
    assert "Codex" in profile["hotwords"]
    assert profile["postprocess"] == {
        "mode": "polished",
        "provider": "local_rules",
        "allow_external_services": False,
    }
    assert "turbo" not in json.dumps(profile).lower()
