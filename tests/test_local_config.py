from pathlib import Path

from ai_operator_controller.local_config import (
    bootstrap_local_config,
    format_local_config_bootstrap,
)


def test_bootstrap_local_config_creates_missing_files(tmp_path):
    project_root = _make_project_root(tmp_path)

    result = bootstrap_local_config(project_root=project_root)

    target_dir = project_root / "config" / "local"
    assert result.target_dir == target_dir
    assert (target_dir / "speech.local-quality.json").read_text(encoding="utf-8") == "speech"
    assert (target_dir / "profile.codex.windows.json").read_text(encoding="utf-8") == "profile"
    assert (target_dir / "replacements.json").read_text(encoding="utf-8") == "rules"
    assert {item.status for item in result.items} == {"created"}


def test_bootstrap_local_config_does_not_overwrite_existing_files(tmp_path):
    project_root = _make_project_root(tmp_path)
    target_dir = project_root / "config" / "local"
    target_dir.mkdir(parents=True)
    existing_rules = target_dir / "replacements.json"
    existing_rules.write_text("private local rules", encoding="utf-8")

    result = bootstrap_local_config(project_root=project_root)

    assert existing_rules.read_text(encoding="utf-8") == "private local rules"
    statuses = {item.destination.name: item.status for item in result.items}
    assert statuses == {
        "speech.local-quality.json": "created",
        "profile.codex.windows.json": "created",
        "replacements.json": "exists",
    }


def test_bootstrap_local_config_resolves_relative_target_under_project_root(tmp_path):
    project_root = _make_project_root(tmp_path)

    result = bootstrap_local_config(
        project_root=project_root,
        local_config_dir=Path("private/config"),
    )

    assert result.target_dir == project_root / "private" / "config"
    assert (project_root / "private" / "config" / "speech.local-quality.json").exists()


def test_format_local_config_bootstrap_prints_next_commands(tmp_path):
    project_root = _make_project_root(tmp_path)
    result = bootstrap_local_config(project_root=project_root)

    output = "\n".join(format_local_config_bootstrap(result))

    assert "Local config bootstrap" in output
    assert "Mode: create missing files only" in output
    assert "[created] Speech profile:" in output
    assert "Existing files were not overwritten." in output
    assert "doctor --profile" in output
    assert "dictate-run --speech-profile" in output


def _make_project_root(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    examples_dir = project_root / "config" / "examples"
    examples_dir.mkdir(parents=True)
    (examples_dir / "speech.local-quality.example.json").write_text("speech", encoding="utf-8")
    (examples_dir / "profile.codex.windows.json").write_text("profile", encoding="utf-8")
    (examples_dir / "replacements.example.json").write_text("rules", encoding="utf-8")
    return project_root
