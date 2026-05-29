import json
from pathlib import Path

import pytest

from ai_operator_controller.config import (
    ProfileValidationError,
    load_profile,
    validate_profile,
)


PROFILE_PATH = Path("config/examples/profile.codex.windows.json")


def test_public_codex_profile_loads_and_validates():
    profile = load_profile(PROFILE_PATH)

    result = validate_profile(profile, source=PROFILE_PATH)

    assert result.profile_name == "codex_windows_default"
    assert "dictate_paste" in result.actions
    assert "cursor_left" in result.actions
    assert result.button_count == 3
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
