from pathlib import Path


START_RUNTIME_SCRIPT = Path("scripts/start-runtime.ps1")


def test_start_runtime_script_defaults_to_read_only_doctor():
    script = START_RUNTIME_SCRIPT.read_text(encoding="utf-8")

    assert '[ValidateSet("doctor", "gamepad-dry-run", "dictation-dry-run", "dictation-execute")]' in script
    assert '[string]$Mode = "doctor"' in script
    assert '"doctor"' in script
    assert "--speech-profile" in script


def test_start_runtime_script_uses_ignored_local_config_by_default():
    script = START_RUNTIME_SCRIPT.read_text(encoding="utf-8")

    assert 'config\\local\\profile.codex.windows.json' in script
    assert 'config\\local\\speech.local-quality.json' in script
    assert 'config\\local\\replacements.json' in script
    assert "Run scripts\\setup-dev.ps1" in script


def test_start_runtime_script_keeps_live_output_behind_confirmation():
    script = START_RUNTIME_SCRIPT.read_text(encoding="utf-8")

    assert "[switch]$ConfirmExecute" in script
    assert "dictation-execute writes to the active window" in script
    assert "--execute-output" in script
    assert "--dry-run" in script
