# AI Operator Controller

[![CI](https://github.com/ryumindmitrii-cmd/ai-operator-controller/actions/workflows/ci.yml/badge.svg)](https://github.com/ryumindmitrii-cmd/ai-operator-controller/actions/workflows/ci.yml)

Local-first voice and gamepad control layer for AI workspaces.

AI Operator Controller is a Windows-first utility for controlling Codex, ChatGPT,
Cursor, browsers, editors, and other AI-heavy tools without staying glued to the
keyboard. It combines push-to-talk dictation, local speech recognition, Xbox
controller mappings, text cleanup, and application-specific command profiles.

## Status

Early project scaffold.

The working private prototype currently lives outside this repository. This repo
is the clean public home where the prototype will be migrated after privacy,
configuration, packaging, and licensing cleanup.

Questions, bug reports, and feature ideas should go through GitHub issues.

## What This Project Is

- A local dictation tool for power users who work inside AI chats all day.
- A controller-first command layer for AI workflows.
- A privacy-first desktop utility: speech is intended to be processed locally by
  default.
- A small, inspectable open-source project, not an enterprise agent platform.

## Target MVP

- Windows-first desktop runtime.
- Push-to-talk dictation using local `faster-whisper`.
- Global hotkeys:
  - `F9`: dictate and paste into the active window.
  - `F8`: dictate to clipboard only.
- Xbox-compatible controller controls:
  - `A`: dictate and paste.
  - `X`: dictate to clipboard.
  - `B`: Backspace; hold to repeat.
  - `LT`: Space.
  - `RT`: Enter.
  - Left stick up/down: move to previous/next chat.
  - Right stick left/right/up/down: move the text cursor.
  - D-pad up/down: scroll the active chat.
- Local text cleanup:
  - replacement dictionary;
  - filler phrase filter;
  - voice commands such as "new line" and "send".
- System tray status indicator.
- App profiles for Codex, ChatGPT, Cursor, browsers, and editors.

## Non-Goals

- Not a general-purpose gamepad mapper.
- Not a full voice-control replacement for Talon or Dragon.
- Not a cloud transcription product.
- Not an agent framework.
- Not tied to one private user's local paths or personal workflows.

## Repository Layout

```text
.
|-- src/ai_operator_controller/   # Python package
|-- config/examples/              # safe public example configs
|-- docs/                         # product, architecture, roadmap, release notes
|-- scripts/                      # future install/dev scripts
|-- tests/                        # test suite
|-- AGENTS.md                     # project rules for AI coding agents
|-- pyproject.toml                # Python packaging metadata
`-- README.md
```

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ai_operator_controller --help
```

## Security Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m bandit -r src
.\.venv\Scripts\python.exe -m pip_audit
.\.venv\Scripts\python.exe -m detect_secrets scan
```

## Public Release Rule

Before the first public GitHub push, run through:

- `docs/public-release-checklist.md`
- `docs/privacy-and-safety.md`
- `docs/migration-from-local-dictation.md`

Do not publish private replacements, local logs, transcripts, `.env` files,
recordings, personal paths, or machine-specific startup shortcuts.
