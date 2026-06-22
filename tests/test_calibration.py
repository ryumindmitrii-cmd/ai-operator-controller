import json
from pathlib import Path

import pytest

from ai_operator_controller.calibration import (
    CalibrationError,
    WindowGeometry,
    calibrate_profile,
    ratios_from_window_point,
)


def test_ratios_from_window_point_uses_window_relative_coordinates():
    ratios = ratios_from_window_point(
        WindowGeometry(left=100, top=50, width=1200, height=800),
        point_x=700,
        point_y=650,
    )

    assert ratios.x_ratio == 0.5
    assert ratios.y_ratio == 0.75


def test_ratios_from_window_point_rejects_point_outside_window():
    with pytest.raises(CalibrationError, match="inside the window"):
        ratios_from_window_point(
            WindowGeometry(left=100, top=50, width=1200, height=800),
            point_x=50,
            point_y=650,
        )


def test_calibrate_profile_updates_focus_target_without_mutating_input():
    profile = {
        "profile_name": "test",
        "hotkeys": {"paste_dictation": "f9", "clipboard_dictation": "f8"},
        "gamepad": {
            "buttons": {
                "a": {
                    "button": 0,
                    "action": "dictate_paste",
                    "focus_before_action": {"target": "message_input"},
                }
            },
            "axes": {},
            "hats": {},
        },
        "focus_targets": {
            "message_input": {
                "strategy": "window_relative_click",
                "x_ratio": 0.5,
                "y_ratio": 0.8,
                "move_caret_to_end": True,
            }
        },
    }

    updated = calibrate_profile(
        profile,
        target="message_input",
        x_ratio=0.45,
        y_ratio=0.86,
    )

    assert profile["focus_targets"]["message_input"]["x_ratio"] == 0.5
    assert updated["focus_targets"]["message_input"] == {
        "strategy": "window_relative_click",
        "x_ratio": 0.45,
        "y_ratio": 0.86,
        "move_caret_to_end": True,
    }


def test_calibrate_profile_creates_new_focus_target():
    profile = json.loads(Path("config/examples/profile.codex.windows.json").read_text())

    updated = calibrate_profile(
        profile,
        target="chat_list",
        x_ratio=0.12,
        y_ratio=0.5,
    )

    assert updated["focus_targets"]["chat_list"] == {
        "strategy": "window_relative_click",
        "x_ratio": 0.12,
        "y_ratio": 0.5,
    }


def test_calibrate_profile_rejects_invalid_ratio():
    profile = json.loads(Path("config/examples/profile.codex.windows.json").read_text())

    with pytest.raises(CalibrationError, match="x_ratio"):
        calibrate_profile(profile, target="message_input", x_ratio=1.1, y_ratio=0.5)
