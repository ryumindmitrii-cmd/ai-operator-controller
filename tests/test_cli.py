import io
from pathlib import Path

from ai_operator_controller.audio_recorder import AudioSampleSummary
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


def test_polish_text_command_polishes_text_from_argument(capsys):
    assert (
        main(
            [
                "polish-text",
                "--text",
                "так смотри я думаю что это можно сделать но надо проверить локально",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Mode: text-polish" in output
    assert "Так, смотри, я думаю, что это можно сделать, но надо проверить локально." in output


def test_clean_text_command_reports_invalid_rules_file(tmp_path, capsys):
    bad_rules = tmp_path / "bad-rules.json"
    bad_rules.write_text('{"replace_phrases": []}', encoding="utf-8")

    assert main(["clean-text", "--rules", str(bad_rules), "--text", "hello"]) == 2

    captured = capsys.readouterr()
    assert "Text cleanup failed" in captured.err
    assert "replace_phrases must be an object" in captured.err


def test_dictate_once_command_runs_preview_paste_pipeline(capsys):
    assert (
        main(
            [
                "dictate-once",
                "--rules",
                "config/examples/replacements.example.json",
                "--text",
                "uh first line new line second line send",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Mode: dictate-once" in output
    assert "Source: transcript" in output
    assert "Action: dictate_paste" in output
    assert "Output target: paste" in output
    assert "Should send: yes" in output
    assert "first line\nsecond line" in output
    assert "write_text: paste length=22" in output
    assert "press_keys: enter" in output


def test_dictate_once_command_supports_clipboard_action(capsys):
    assert (
        main(
            [
                "dictate-once",
                "--dictation-action",
                "dictate_clipboard",
                "--rules",
                "config/examples/replacements.example.json",
                "--text",
                "uh clipboard only send",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Action: dictate_clipboard" in output
    assert "Output target: clipboard" in output
    assert "Should send: yes" in output
    assert "write_text: clipboard length=14" in output
    assert "press_keys: enter" not in output


def test_dictate_once_command_reports_blocked_auto_send(capsys):
    assert (
        main(
            [
                "dictate-once",
                "--rules",
                "config/examples/replacements.example.json",
                "--transcription-confidence",
                "0.2",
                "--text",
                "please review this send",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Should send: yes" in output
    assert "Auto-send: no" in output
    assert "Review required: yes" in output
    assert "Quality confidence: low" in output
    assert "low_transcription_confidence" in output
    assert "press_keys: enter" not in output


def test_record_once_requires_dry_run(capsys):
    assert main(["record-once", "--seconds", "0.1"]) == 2

    captured = capsys.readouterr()
    assert "Record preview failed" in captured.err
    assert "--dry-run is required" in captured.err


def test_record_once_command_prints_safe_audio_metadata(capsys, monkeypatch):
    def fake_record_microphone_once(*, seconds, sample_rate, channels, device):
        assert seconds == 0.5
        assert sample_rate == 16000
        assert channels == 1
        assert device is None
        return AudioSampleSummary(
            sample_rate=16000,
            frame_count=8000,
            channel_count=1,
            dtype="float32",
            duration_seconds=0.5,
            rms=0.125,
            peak_abs=0.5,
        )

    monkeypatch.setattr(
        "ai_operator_controller.cli.record_microphone_once",
        fake_record_microphone_once,
    )

    assert main(["record-once", "--seconds", "0.5", "--dry-run"]) == 0

    output = capsys.readouterr().out
    assert "Mode: record-once" in output
    assert "Dry-run: yes" in output
    assert "Saved file: no" in output
    assert "Duration: 0.500s" in output
    assert "Sample rate: 16000 Hz" in output
    assert "Channels: 1" in output
    assert "Frames: 8000" in output
    assert "RMS: 0.125000" in output
    assert "Peak: 0.500000" in output
    assert "Text:" not in output


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
    assert "Action: focus_message_pane" in output
    assert "focus_mouse_target: message_pane click=True" in output


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


def test_simulate_gamepad_bumper_button_prints_mouse_click(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--button",
                "rb",
                "down",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Input: button rb down" in output
    assert "Action: mouse_right_click" in output
    assert "click_mouse: right" in output


def test_simulate_gamepad_panel_buttons_print_keyboard_shortcuts(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--button",
                "y",
                "down",
            ]
        )
        == 0
    )

    sidebar_output = capsys.readouterr().out
    assert "Action: toggle_sidebar" in sidebar_output
    assert "press_keys: ctrl+alt+b" in sidebar_output

    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--button",
                "menu",
                "down",
            ]
        )
        == 0
    )

    bottom_panel_output = capsys.readouterr().out
    assert "Action: toggle_bottom_panel" in bottom_panel_output
    assert "press_keys: ctrl+j" in bottom_panel_output


def test_simulate_gamepad_scroll_axis_prints_dry_run_event(capsys):
    assert (
        main(
            [
                "simulate-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
                "--axis",
                "right_stick_y",
                "0.8",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Input: axis right_stick_y 0.8" in output
    assert "Action: scroll_down" in output
    assert "scroll: -0.25" in output


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


def test_listen_gamepad_requires_dry_run(capsys):
    assert (
        main(
            [
                "listen-gamepad",
                "--profile",
                "config/examples/profile.codex.windows.json",
            ]
        )
        == 2
    )

    captured = capsys.readouterr()
    assert "Gamepad listener failed" in captured.err
    assert "--dry-run is required" in captured.err
