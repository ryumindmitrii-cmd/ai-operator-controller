from pathlib import Path


SETUP_SCRIPT = Path("scripts/setup-dev.ps1")


def test_setup_script_checks_python_version_before_creating_venv():
    script = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert "Invoke-PythonVersionCheck" in script
    assert "sys.version_info < (3, 11)" in script
    assert "Python 3.11 or newer is required" in script


def test_setup_script_bootstraps_local_config_and_runs_doctor():
    script = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert "init-local-config" in script
    assert "config\\local\\profile.codex.windows.json" in script
    assert "config\\local\\speech.local-quality.json" in script
    assert "doctor" in script


def test_setup_script_prints_first_run_next_steps():
    script = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert "Next checks:" in script
    assert "record-once --seconds 2 --dry-run" in script
    assert "listen-gamepad --profile $LocalProfile" in script
