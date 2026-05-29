from pathlib import Path

from ai_operator_controller.cli import main


def test_version_command(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_doctor_profile_command_reports_profile_status(capsys):
    assert main(["doctor", "--profile", "config/examples/profile.codex.windows.json"]) == 0

    output = capsys.readouterr().out
    assert "Profile: codex_windows_default" in output
    assert "Actions: valid" in output
    assert "Gamepad mapping: valid" in output
    assert "Focus targets: valid" in output
    assert "Private/local markers: none detected" in output


def test_doctor_profile_command_reports_validation_errors(tmp_path, capsys):
    bad_profile = tmp_path / "bad-profile.json"
    bad_profile.write_text(
        Path("config/examples/profile.codex.windows.json")
        .read_text()
        .replace('"action": "dictate_paste"', '"action": "unknown_action"', 1)
    )

    assert main(["doctor", "--profile", str(bad_profile)]) == 2

    captured = capsys.readouterr()
    assert "Profile validation failed" in captured.err
    assert "Unknown action" in captured.err
