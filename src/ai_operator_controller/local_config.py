from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Literal


BootstrapStatus = Literal["created", "exists"]


@dataclass(frozen=True)
class LocalConfigTemplate:
    label: str
    source_name: str
    destination_name: str


@dataclass(frozen=True)
class LocalConfigItem:
    label: str
    source: Path
    destination: Path
    status: BootstrapStatus


@dataclass(frozen=True)
class LocalConfigBootstrapResult:
    target_dir: Path
    items: tuple[LocalConfigItem, ...]


class LocalConfigBootstrapError(RuntimeError):
    """Raised when public example files required for local config are missing."""


LOCAL_CONFIG_TEMPLATES = (
    LocalConfigTemplate(
        label="Speech profile",
        source_name="speech.local-quality.example.json",
        destination_name="speech.local-quality.json",
    ),
    LocalConfigTemplate(
        label="Codex profile",
        source_name="profile.codex.windows.json",
        destination_name="profile.codex.windows.json",
    ),
    LocalConfigTemplate(
        label="Text cleanup rules",
        source_name="replacements.example.json",
        destination_name="replacements.json",
    ),
)


def bootstrap_local_config(
    *,
    project_root: Path | None = None,
    local_config_dir: Path | None = None,
) -> LocalConfigBootstrapResult:
    root = Path.cwd() if project_root is None else project_root
    examples_dir = root / "config" / "examples"
    if local_config_dir is None:
        target_dir = root / "config" / "local"
    elif local_config_dir.is_absolute():
        target_dir = local_config_dir
    else:
        target_dir = root / local_config_dir

    items = []
    for template in LOCAL_CONFIG_TEMPLATES:
        source = examples_dir / template.source_name
        if not source.is_file():
            raise LocalConfigBootstrapError(f"missing public example config: {source}")

        destination = target_dir / template.destination_name
        if destination.exists():
            items.append(
                LocalConfigItem(
                    label=template.label,
                    source=source,
                    destination=destination,
                    status="exists",
                )
            )
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        items.append(
            LocalConfigItem(
                label=template.label,
                source=source,
                destination=destination,
                status="created",
            )
        )

    return LocalConfigBootstrapResult(target_dir=target_dir, items=tuple(items))


def format_local_config_bootstrap(result: LocalConfigBootstrapResult) -> list[str]:
    lines = [
        "Local config bootstrap",
        "Mode: create missing files only",
        "Safety: Existing files were not overwritten.",
        f"Target: {_display_path(result.target_dir)}",
    ]
    for item in result.items:
        lines.append(f"[{item.status}] {item.label}: {_display_path(item.destination)}")

    paths = {item.destination.name: _display_path(item.destination) for item in result.items}
    speech_profile = paths["speech.local-quality.json"]
    codex_profile = paths["profile.codex.windows.json"]
    replacements = paths["replacements.json"]
    lines.extend(
        [
            "Next commands:",
            f"- python -m ai_operator_controller doctor --profile {codex_profile} "
            f"--speech-profile {speech_profile}",
            f"- python -m ai_operator_controller dictate-run --speech-profile {speech_profile} "
            f"--rules {replacements} --dry-run",
        ]
    )
    return lines


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
