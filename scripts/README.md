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
