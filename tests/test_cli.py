import io
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


def test_plan_action_command_prints_dry_run_event(capsys):
    assert main(["plan-action", "cursor_left"]) == 0

    output = capsys.readouterr().out
    assert "Action: cursor_left" in output
    assert "press_keys: left" in output


def test_plan_action_command_reports_unsupported_actions(capsys):
    assert main(["plan-action", "dictate_paste"]) == 2

    captured = capsys.readouterr()
    assert "Action planning failed" in captured.err
    assert "dictate_paste" in captured.err


def test_clean_text_command_cleans_text_from_argument(capsys):
    assert (
        main(
            [
                "clean-text",
                "--rules",
                "config/examples/replacements.example.json",
                "--text",
                "uh first line new line second line send",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Mode: text-cleanup" in output
    assert "Should send: yes" in output
    assert "first line\nsecond line" in output


def test_clean_text_command_cleans_text_from_stdin(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("um label colon value"))

    assert (
        main(
            [
                "clean-text",
                "--rules",
                "config/examples/replacements.example.json",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Should send: no" in output
    assert "label: value" in output


def test_clean_text_command_reports_invalid_rules_file(tmp_path, capsys):
    bad_rules = tmp_path / "bad-rules.json"
    bad_rules.write_text('{"replace_phrases": []}', encoding="utf-8")

    assert main(["clean-text", "--rules", str(bad_rules), "--text", "hello"]) == 2

    captured = capsys.readouterr()
    assert "Text cleanup failed" in captured.err
    assert "replace_phrases must be an object" in captured.err


def test_simulate_gamepad_axis_prints_dry_run_event(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--axis",
                "right_stick_x",
                "0.8",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Input: axis right_stick_x 0.8" in output
    assert "Action: cursor_right" in output
    assert "press_keys: right" in output


def test_simulate_gamepad_button_reports_future_dictation_action(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--button",
                "a",
                "down",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Action: dictate_paste" in output
    assert "Output: unsupported" in output


def test_simulate_gamepad_hat_prints_dry_run_event(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--hat",
                "dpad",
                "0",
                "-1",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Input: hat dpad 0 -1" in output
    assert "Action: scroll_down" in output
    assert "scroll: -3" in output


def test_simulate_gamepad_reports_unknown_input_name(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--axis",
                "missing_axis",
                "0.8",
            ]
        )
        == 2
    )

    captured = capsys.readouterr()
    assert "unknown gamepad axis: missing_axis" in captured.err
