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
.\.venv\Scripts\python.exe -m ai_operator_controller plan-action cursor_left
.\.venv\Scripts\python.exe -m ai_operator_controller plan-action focus_message_pane
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_x 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_y 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller clean-text --rules config\examples\replacements.example.json --text "uh first line new line second line send"
.\.venv\Scripts\python.exe -m ai_operator_controller dictate-once --rules config\examples\replacements.example.json --text "uh first line new line second line send"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests
```

Expected result:

- `doctor` prints that the scaffold is installed.
- `doctor --profile` reports that the Codex profile actions, gamepad mapping,
  focus targets, and private/local marker checks are valid.
- `plan-action` prints dry-run output events without sending real keyboard,
  mouse, or scroll input.
- `simulate-gamepad` resolves profile-based controller inputs into actions and
  dry-run output events.
- `clean-text` prints cleaned dictation text and whether a trailing send command
  was detected.
- `dictate-once` runs the preview dictation pipeline from transcript text to
  dry-run output without recording audio or sending keyboard input.
- Tests pass.
- Ruff reports no lint issues.

If a controller is connected, run:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller listen-gamepad --profile config\examples\profile.codex.windows.json --dry-run --max-events 5
```

Press mapped controls such as `B`, right stick, or D-pad. The command prints
mapped actions and stops after five emitted actions.

## Current Public Capabilities

- Safe public Codex Windows profile:
  `config/examples/profile.codex.windows.json`.
- Profile loading and validation through `ai_operator_controller doctor
  --profile`.
- Dry-run output planning through `ai_operator_controller plan-action`.
- Profile-driven gamepad simulation through `ai_operator_controller
  simulate-gamepad`.
- Physical gamepad dry-run listening through `ai_operator_controller
  listen-gamepad --dry-run`.
- Text cleanup through `ai_operator_controller clean-text`.
- Preview dictation runtime through `ai_operator_controller dictate-once`.
- Text cleanup and replacement-rule tests.
- Controller mapping logic for sticks, buttons, D-pad cursor movement, and semantic
  actions.
- Output planning for keyboard, mouse, scroll, and focus actions.
- CLI scaffold and project structure for the upcoming full runtime.

## Current Limitations

- No Windows tray app or installer yet.
- The public package does not yet run the full push-to-talk dictation loop.
- `dictate-once` uses transcript text as input; microphone recording and local
  faster-whisper transcription are still being migrated.
- `listen-gamepad --dry-run` reads a physical controller but intentionally does
  not send real keyboard, mouse, clipboard, or dictation output.
- The private prototype is not copied into this repository until logs, local
  paths, recordings, dictionaries, and machine-specific scripts are sanitized.

## Controller Profile Notes

The default Codex example profile uses these high-frequency controls:

- `A`: focus near the lower-center message input, move the caret to the end, and
  start paste-mode dictation.
- `X`: paste-mode dictation at the current text cursor without moving focus.
- `B`: Backspace with hold-to-repeat.
- `LB`: left mouse click.
- `RB`: right mouse click.
- `LT`: Space.
- `RT`: Enter.
- Left stick up/down: previous or next chat.
- D-pad: text cursor movement.
- Right stick left/right: choose chat-list or message-pane scroll target.
- Right stick up/down: scroll the selected target, with repeat speed scaled by
  stick intensity.

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

## Simulate Gamepad Inputs

These commands exercise the public profile without reading a physical controller
or sending real desktop input:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_x 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button b down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_y 0.8
```

Dictation actions such as `A` are reported as future runtime actions in this
preview. They do not start recording yet.

## Clean Text

Run the public example replacement rules against a short dictation sample:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller clean-text --rules config\examples\replacements.example.json --text "uh first line new line second line send"
```

Expected output includes:

```text
Mode: text-cleanup
Should send: yes
Text:
first line
second line
```

For longer text, pipe stdin instead of putting the text in the command history:

```powershell
"um label colon value" | .\.venv\Scripts\python.exe -m ai_operator_controller clean-text --rules config\examples\replacements.example.json
```

Use `config\examples\replacements.example.json` as a template only. Personal
names, phrases, chat snippets, and private vocabulary should stay in ignored
local config files, not in commits or issue reports.

## Dictation Pipeline Preview

Run the first public dictation pipeline without a microphone:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller dictate-once --rules config\examples\replacements.example.json --text "uh first line new line second line send"
```

Expected output includes:

```text
Mode: dictate-once
Source: transcript
Action: dictate_paste
Output target: paste
Should send: yes
Text:
first line
second line
Dry-run output:
write_text: paste length=22
press_keys: enter
```

Clipboard-only preview:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller dictate-once --dictation-action dictate_clipboard --rules config\examples\replacements.example.json --text "uh clipboard only send"
```

This command is intentionally dry-run only in the public preview. It does not
listen to the microphone, write to the clipboard, paste into applications, or
press Enter.

## Physical Controller Dry Run

You can connect an Xbox-compatible controller to a laptop and verify the public
profile mapping without sending real desktop input:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller doctor --profile config\examples\profile.codex.windows.json
.\.venv\Scripts\python.exe -m ai_operator_controller listen-gamepad --profile config\examples\profile.codex.windows.json --dry-run --max-events 10
```

Expected output shape:

```text
Controller: Xbox Controller
Mode: dry-run
Listening for mapped gamepad actions. Press Ctrl+C to stop.
Input: button b down
Action: backspace
press_keys: backspace
```

If no controller is detected, reconnect it and rerun the command. Use
`--gamepad-index 1` if Windows exposes the controller as a non-default device.

## Privacy Rule

Do not commit local logs, recordings, transcripts, private replacement
dictionaries, `.env` files, tokens, credentials, or personal startup shortcuts.
Use synthetic examples when opening issues or sharing screenshots.
