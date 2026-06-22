# Public Release Checklist

Use this before tagging or publishing `v0.1.0`.

Last readiness update: 2026-06-22.

Scope: `v0.1.0` is a Windows Codex Desktop local preview. It does not include a
ChatGPT browser profile, Cursor profile, generic browser profile, installer,
tray app, cloud transcription, account login automation, or automatic learning
from private chat history.

## Repository Hygiene

- [x] `git status` shows only intentional files.
- [x] `.gitignore` excludes virtualenvs, logs, audio, transcripts, secrets, and local configs.
- [x] No `.env`, token, credential, or auth files are tracked.
- [x] No private recordings or transcripts are tracked.
- [x] No personal replacement dictionary is tracked.
- [x] No local startup shortcut or machine-specific launcher is tracked.
- [x] `config/local/`, `_drafts/`, logs, audio, and generated local reports are
  untracked or ignored.

## Content Review

- [x] README describes the project accurately.
- [x] README does not claim features that are not implemented.
- [x] README and release notes state that `v0.1.0` is Codex Desktop first.
- [x] Browser/ChatGPT/Cursor profiles are described only as future work.
- [x] Public examples use synthetic data.
- [x] Screenshots/videos, if any, contain no private chats.
- [x] License is present.
- [x] Security/private data policy is present.
- [x] `docs/release-notes-v0.1.0.md` lists known limitations and rollback path.

## Technical Review

- [x] `python -m compileall src tests` passes.
- [x] Unit tests pass.
- [x] `python -m ruff check src tests` passes.
- [x] The CLI help command runs.
- [x] `scripts\smoke.ps1 -BypassProxyForPipAudit` passes, or any skipped step is
  explicitly documented.
- [x] `docs\codex-profile-checklist.md` has been run against Codex Desktop, or
  unverified live items are listed before release.
- [x] GitHub Actions CI is green on `main`.

## GitHub Release

- [ ] Dmitrii confirms the exact tag: `v0.1.0`.
- [ ] Dmitrii confirms the GitHub release title and notes.
- [ ] No tag is pushed before explicit confirmation.
- [ ] No GitHub release is created before explicit confirmation.
