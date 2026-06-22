# Codex Windows Profile Checklist

Use this checklist to verify the public Codex Desktop controller profile on a
Windows machine without sending live keyboard or mouse input.

The checklist is intentionally split into dry-run checks and manual live checks.
Dry-run checks prove the public profile resolves controller inputs into the
documented actions. Manual live checks are still required before claiming that a
physical Codex session works end to end.

## Maintainer Validation Status

On 2026-06-22, the maintainer ran a physical controller dry-run against the
public Codex mapping contract and then manually confirmed live Codex Desktop
controller behavior on the maintainer Windows setup.

This is release-candidate evidence for the first maintainer setup, not a
guarantee for every monitor, Windows scaling setting, controller driver, or
Codex Desktop layout. New machines should still run this checklist locally
before enabling live output.

## Safety Boundaries

- Use `--dry-run` first. Dry-run mode must not send keyboard, mouse, clipboard,
  or dictation output to another application.
- Do not run microphone or live-output commands with private transcripts,
  recordings, logs, or local replacement dictionaries in this repository.
- `A` and `X` map to `dictate_paste`, but the gamepad dry-run listener currently
  reports them as future runtime actions. It does not start recording from
  `listen-gamepad --dry-run`.
- Keep local overrides in `config/local/`; do not edit
  `config/examples/profile.codex.windows.json` for one machine.

## Setup Check

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode doctor
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode gamepad-dry-run -GamepadMaxEvents 20
```

The doctor command should report package, audio input, speech runtime, profile,
and controller status. A CUDA warning is acceptable on machines without a CUDA
GPU.

The gamepad dry-run command should print the controller name and mapped actions
when you press or move the controls below.

## Mapping Contract

| Control | Expected action | Expected dry-run output |
| --- | --- | --- |
| `A` | `dictate_paste` | Unsupported future action; no output event |
| `X` | `dictate_paste` | Unsupported future action; no output event |
| `B` | `backspace` | `press_keys: backspace` |
| hold `B` | repeated `backspace` | repeats after the configured cooldown |
| `LB` | `mouse_left_click` | `click_mouse: left` |
| `RB` | `mouse_right_click` | `click_mouse: right` |
| `LT` | `space` | `press_keys: space` |
| `RT` | `enter` | `press_keys: enter` |
| `Y` | `toggle_sidebar` | `press_keys: ctrl+alt+b` |
| Menu/Start | `toggle_bottom_panel` | `press_keys: ctrl+j` |
| left stick up | `chat_previous` | `press_keys: ctrl+shift+tab` |
| left stick down | `chat_next` | `press_keys: ctrl+tab` |
| right stick left | `focus_chat_list` | `focus_mouse_target: chat_list click=False` |
| right stick right | `focus_message_pane` | `focus_mouse_target: message_pane click=True` |
| right stick up | `scroll_up` | `scroll: 0.25` |
| right stick down | `scroll_down` | `scroll: -0.25` |
| D-pad up | `cursor_up` | `press_keys: up` |
| D-pad down | `cursor_down` | `press_keys: down` |
| D-pad left | `cursor_left` | `press_keys: left` |
| D-pad right | `cursor_right` | `press_keys: right` |

## Simulated Checks

These commands validate the public profile without a physical controller:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button a down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button x down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button b down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button lb down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button rb down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button y down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button menu down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis lt 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis rt 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis left_stick_y -0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis left_stick_y 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_x -0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_x 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_y -0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --axis right_stick_y 0.8
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --hat dpad 0 1
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --hat dpad 0 -1
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --hat dpad -1 0
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --hat dpad 1 0
```

## Manual Live Checklist

Run these only after the dry-run checks match the mapping contract.

- Start Codex Desktop and focus a normal chat draft.
- Keep any send/Enter action disabled or under direct manual control until you
  intentionally test it.
- Press `A`: the cursor should land near the lower-center message input and move
  to the end of existing text before dictation/paste mode is used.
- Press `X`: dictation/paste mode should use the current text cursor position
  without moving focus first.
- Hold `B`: text should delete repeatedly at the configured repeat pace.
- Use D-pad directions: the text cursor should move one step per action.
- Use right stick left/right: the mouse target should switch between chat list
  and message pane without unexpectedly changing text-input focus.
- Use right stick up/down: the selected area should scroll in the expected
  direction.
- Use left stick up/down: chat navigation should move only between chats and
  should not open settings or leave the current workspace unexpectedly.
- Use `Y` and Menu/Start: the Codex sidebar and bottom panel should toggle with
  the documented shortcuts.
- Use `LB` and `RB` only where mouse clicks are safe.

Record any mismatch as:

```text
Control:
Expected:
Observed:
Window/app:
Dry-run output:
Recovery path:
```

Do not include private transcripts, screenshots, recordings, logs, or local
paths in public issues.
