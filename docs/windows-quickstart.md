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
- Optional: NVIDIA GPU for the default local `faster-whisper` quality profile.
  The public quality speech profile uses `large-v3` on CUDA/float16 by default;
  CPU users can copy the example profile and override device and compute type.

## Install From GitHub

```powershell
git clone https://github.com/ryumindmitrii-cmd/ai-operator-controller.git
cd ai-operator-controller
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
```

## Smoke Test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithMicrophone
```

The first command skips microphone access. The second command includes the
metadata-only microphone check.

Expected result:

- `doctor` prints a read-only runtime report for Python, package import, audio
  input visibility, speech runtime, CUDA/compute-type status, and gamepad
  visibility.
- `doctor --profile` also reports that the Codex profile actions, gamepad
  mapping, focus targets, and private/local marker checks are valid.
- `plan-action` prints dry-run output events without sending real keyboard,
  mouse, or scroll input.
- `simulate-gamepad` resolves profile-based controller inputs into actions and
  dry-run output events.
- `record-once --dry-run` records a short microphone sample and prints only
  metadata such as duration, frames, RMS, and peak level. It does not save audio
  or transcribe it.
- `clean-text` prints cleaned dictation text and whether a trailing send command
  was detected.
- `polish-text` prints locally polished punctuation for dictated text without
  using a network service.
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
- Safe public local speech quality profile:
  `config/examples/speech.local-quality.example.json`.
- Read-only runtime checks through `ai_operator_controller doctor`.
- Profile loading and validation through `ai_operator_controller doctor
  --profile`.
- Dry-run output planning through `ai_operator_controller plan-action`.
- Profile-driven gamepad simulation through `ai_operator_controller
  simulate-gamepad`.
- Physical gamepad dry-run listening through `ai_operator_controller
  listen-gamepad --dry-run`.
- Microphone metadata dry-run through `ai_operator_controller record-once
  --dry-run`.
- Local file transcription dry-run through `ai_operator_controller
  transcribe-file --dry-run`.
- Local microphone-to-output pipeline dry-run through `ai_operator_controller
  dictate-run --dry-run`.
- Explicit Windows output execution through `ai_operator_controller dictate-run
  --execute-output` after the user focuses a safe target window.
- Text cleanup through `ai_operator_controller clean-text`.
- Preview dictation runtime through `ai_operator_controller dictate-once`.
- Text cleanup and replacement-rule tests.
- Controller mapping logic for sticks, buttons, D-pad cursor movement, and semantic
  actions.
- Output planning for keyboard, mouse, scroll, and focus actions.
- CLI scaffold and project structure for the upcoming full runtime.

## Runtime Doctor

Run the read-only runtime diagnostic before microphone or controller tests:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller doctor --profile config\examples\profile.codex.windows.json --speech-profile config\examples\speech.local-quality.example.json
```

Expected output shape:

```text
AI Operator Controller doctor
Mode: read-only diagnostics
Safety: No audio was recorded. No clipboard or keyboard output was sent.
[ok] Package: ...
[ok] Audio: input devices: ...
[ok] Speech profile: ...
[ok] Speech runtime: ...
[warning] Gamepad: detected: 0
[ok] Profile: codex_windows_default; Actions: valid ...
```

Warnings are actionable setup signals, not live desktop actions. For example, a
gamepad warning means Windows does not currently expose a controller to
`pygame`. Rerun with `--mic-device <INDEX>` or `--gamepad-index <INDEX>` when
Windows exposes multiple devices. The command may print local device names to
the terminal, but it does not save them to the repository or send them anywhere.

## Current Limitations

- No Windows tray app or installer yet.
- The public package can run one microphone-to-transcript-to-output command, but
  does not yet run the full push-to-talk hotkey/controller dictation loop.
- `listen-gamepad --dry-run` reads a physical controller but intentionally does
  not send real keyboard, mouse, clipboard, or dictation output.
- The private prototype is not copied into this repository until logs, local
  paths, recordings, dictionaries, and machine-specific scripts are sanitized.

## Controller Profile Notes

The default Codex example profile uses these high-frequency controls:

- `A`: focus near the lower-center message input, move the caret to the end, and
  start paste-mode dictation.
- `X`: paste-mode dictation at the current text cursor without moving focus.
- `Y`: toggle the Codex side bar with `Ctrl+Alt+B`.
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
- Menu/Start: toggle the bottom panel with `Ctrl+J`.

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
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button y down
.\.venv\Scripts\python.exe -m ai_operator_controller simulate-gamepad --profile config\examples\profile.codex.windows.json --button menu down
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

## Polish Text

Run the local deterministic punctuation polish layer:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller polish-text --text "так смотри я думаю что это можно сделать но надо проверить локально"
```

Expected output includes:

```text
Mode: text-polish
Text:
Так, смотри, я думаю, что это можно сделать, но надо проверить локально.
```

This pass is local-only. It adjusts punctuation, spacing, and sentence
capitalization, but it is not allowed to add new content or send dictated text to
an external service.

## Microphone Record Dry Run

Run a short microphone diagnostic without saving audio, transcribing speech, or
sending desktop input:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller record-once --seconds 2 --dry-run
```

Expected output shape:

```text
Mode: record-once
Dry-run: yes
Saved file: no
Duration: 2.000s
Sample rate: 16000 Hz
Channels: 1
Frames: 32000
Dtype: float32
RMS: 0.012345
Peak: 0.123456
```

This command is only a microphone smoke test. It does not write `.wav` files,
does not print or store transcripts, and does not interact with the clipboard or
keyboard.

## Local File Transcription Dry Run

Run a local `faster-whisper` speech profile against an explicit audio file:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller transcribe-file --speech-profile config\examples\speech.local-quality.example.json --audio-file <PATH_TO_WAV> --dry-run
```

Expected output shape:

```text
Mode: transcribe-file
Dry-run: yes
Saved file: no
Model: large-v3
Device: cuda
Compute type: float16
VAD filter: enabled
Fallback used: no
Model download: disabled
Language: ru
Language probability: 0.987
Duration: 3.210s
Segments: 1
Text:
...
```

Model downloads are disabled by default so this command fails clearly if the
model is not already available locally. Add `--allow-model-download` only when
you intentionally want `faster-whisper` to fetch model files. The command does
not save audio, write clipboard content, or send keyboard input, but it does
print the transcript to the terminal.

## Dictation Pipeline Preview

Run the local microphone-to-output dry-run pipeline:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller dictate-run --seconds 2 --rules config\examples\replacements.example.json --dry-run
```

Expected output shape:

```text
Mode: dictate-run
Dry-run: yes
Saved audio: no
Source: microphone
Audio duration: 2.000s
Transcription model: large-v3
Transcription VAD filter: enabled
Action: dictate_paste
Output target: paste
Should send: no
Auto-send: no
Text:
...
Dry-run output:
write_text: paste length=...
```

This command records to a temporary local file, transcribes it, applies cleanup
and the quality gate, prints planned output events, and deletes the temporary
file. It does not write clipboard content, paste into applications, or press
Enter.

To test the first real Windows output path, focus a safe scratch window such as
an empty Notepad document, then run:

```powershell
.\.venv\Scripts\python.exe -m ai_operator_controller dictate-run --seconds 2 --rules config\examples\replacements.example.json --execute-output
```

This is intentionally not a default smoke check. It writes the dictated text to
the clipboard, sends `Ctrl+V` to the active window, and presses `Enter` only
when the quality gate allows auto-send. Terminal output hides the dictated text
and prints metadata-only output events:

```text
Mode: dictate-run
Dry-run: no
Execute output: yes
Saved audio: no
...
Text: <hidden; length=...>
Output events:
write_text: paste length=...
```

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
Auto-send: yes
Review required: no
Quality confidence: high
Quality reasons: none
Text:
first line
second line
Dry-run output:
write_text: paste length=22
press_keys: enter
```

`Should send` means the cleanup layer recognized a trailing voice command such
as "send". `Auto-send` is the stricter quality-gate decision. It stays `no` and
does not plan `press_keys: enter` when optional recognition confidence is low,
the text is long, or local polishing changed the text too much.

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
