# Scripts

Portable helper scripts for local setup and verification.

Scripts in this repository must be portable examples. Machine-specific scripts
with hard-coded personal paths should stay in local/private config.

## Development Environment

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
```

This creates `.venv`, upgrades `pip`, installs the project in editable mode with
development dependencies, and verifies that the CLI imports.

## Smoke Checks

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1
```

This runs CLI dry-runs, tests, lint, compile checks, whitespace checks, privacy
marker scanning, `detect-secrets`, `bandit`, and `pip-audit`.

To include the metadata-only microphone smoke test:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithMicrophone
```

The microphone smoke test does not save audio, print transcripts, touch the
clipboard, or send keyboard input.

To include a real local `faster-whisper` model check, provide an explicit local
audio file:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithSpeechModel -SpeechAudioPath <PATH_TO_WAV>
```

By default this does not download a missing model. Add `-AllowModelDownload` only
when you are intentionally allowing `faster-whisper` to fetch model files. The
audio file and transcript are never saved by the script, but the transcript is
printed to the terminal as part of the manual check.

To include the full local dry-run pipeline from microphone to planned output
events:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithDictateRun
```

This records a temporary microphone sample, transcribes it locally, applies text
cleanup and the quality gate, prints dry-run output events, and deletes the
temporary audio file. It still does not touch the clipboard or send keyboard
input.
