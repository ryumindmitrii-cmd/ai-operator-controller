# Project Agent Rules: AI Operator Controller

## Purpose

This project builds a public open-source local control layer for AI workspaces:
voice dictation, gamepad controls, hotkeys, local text cleanup, and app profiles
for tools such as Codex, ChatGPT, Cursor, browsers, and editors.

## Boundaries

- Treat this as a public repository from day one.
- Do not copy private logs, transcripts, recordings, personal replacement
  dictionaries, `.env` files, OAuth tokens, API keys, or machine-specific paths.
- Do not publish to GitHub, create a remote repository, push commits, open
  releases, or submit packages without explicit confirmation from Dmitrii.
- Keep the existing private prototype outside this repository as source context
  only. Migrate code deliberately and sanitize it before committing.
- Prefer configuration files and examples over hard-coded local behavior.

## Default Technical Direction

- Windows-first.
- Python package first; keep room for a later native tray/GUI wrapper.
- Local speech recognition first, using `faster-whisper`.
- Controller input through `pygame`/SDL initially.
- Keyboard injection through Windows `SendInput` with fallback where needed.
- Config-driven profiles for hotkeys, controller mappings, and text cleanup.

## Quality Rules

- Keep changes small and reversible.
- Add tests for parsing, command mapping, and text cleanup before broad refactors.
- Separate public examples from private user config.
- Public docs should be in English unless a file is explicitly for Dmitrii's
  private project management.
- Avoid hidden network calls. Any cloud transcription mode must be opt-in and
  clearly documented.

## Verification

For non-trivial changes, finish with at least one concrete check:

- `python -m compileall src tests`
- unit tests;
- manual runtime status/log evidence;
- screenshot only if a UI exists.

## Public GitHub Readiness

Before public release, verify:

- license is present;
- README is clear and accurate;
- private paths are absent from committed code/docs except documented examples
  that are explicitly marked as local/private and not default behavior;
- `.gitignore` excludes logs, audio, virtualenvs, configs, secrets, and local
  machine artifacts;
- no real API keys, tokens, chat logs, or recordings are in the repo.
