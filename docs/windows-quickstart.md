# Windows Quick Start

This is an early public developer preview. The repository is ready for code
review, local installation of the Python package scaffold, tests, and profile
experiments. The full dictation runtime is still being migrated from the private
prototype after privacy cleanup.

## Requirements

- Windows 10 or Windows 11.
- Python 3.11 or 3.12.
- Git.
- An Xbox-compatible controller for controller mapping experiments.
- Optional: NVIDIA GPU for future local `faster-whisper` use.

## Install From GitHub

```powershell
git clone https://github.com/ryumindmitrii-cmd/ai-operator-controller.git
cd ai-operator-controller
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Smoke Test

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller --help
.\.venv\Scripts\python.exe -m ai_operator_controller doctor
.\.venv\Scripts\python.exe -m ai_operator_controller doctor --profile config\examples\profile.codex.windows.json
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

Expected result:

- `doctor` prints that the scaffold is installed.
- `doctor --profile` reports that the Codex profile actions, gamepad mapping,
  focus targets, and private/local marker checks are valid.
- Tests pass.
- Ruff reports no lint issues.

## Current Public Capabilities

- Safe public Codex Windows profile:
  `config/examples/profile.codex.windows.json`.
- Profile loading and validation through `ai_operator_controller doctor
  --profile`.
- Text cleanup and replacement-rule tests.
- Controller mapping logic for sticks, buttons, D-pad scrolling, and semantic
  actions.
- Output planning for keyboard, mouse, scroll, and focus actions.
- CLI scaffold and project structure for the upcoming full runtime.

## Current Limitations

- No Windows tray app or installer yet.
- The public package does not yet run the full push-to-talk dictation loop.
- The private prototype is not copied into this repository until logs, local
  paths, recordings, dictionaries, and machine-specific scripts are sanitized.

## Controller Profile Notes

The default Codex example profile uses these high-frequency controls:

- `A`: focus near the lower-center message input, move the caret to the end, and
  start paste-mode dictation.
- `X`: clipboard-only dictation.
- `B`: Backspace with hold-to-repeat.
- `LT`: Space.
- `RT`: Enter.
- Left stick up/down: previous or next chat.
- Right stick: text cursor movement.
- D-pad left/right: choose chat-list or message-pane scroll target.
- D-pad up/down: scroll the selected target.

The `A` focus target is intentionally configurable:

```json
"focus_before_action": {
  "target": "message_input",
  "strategy": "lower_center_click",
  "x_ratio": 0.5,
  "bottom_offset_pixels": 100,
  "move_caret_to_end": true
}
```

## Privacy Rule

Do not commit local logs, recordings, transcripts, private replacement
dictionaries, `.env` files, tokens, credentials, or personal startup shortcuts.
Use synthetic examples when opening issues or sharing screenshots.
