# Public Release Checklist

Use this before tagging or publishing `v0.1.0`.

Scope: `v0.1.0` is a Windows Codex Desktop local preview. It does not include a
ChatGPT browser profile, Cursor profile, generic browser profile, installer,
tray app, cloud transcription, account login automation, or automatic learning
from private chat history.

## Repository Hygiene

- [ ] `git status` shows only intentional files.
- [ ] `.gitignore` excludes virtualenvs, logs, audio, transcripts, secrets, and local configs.
- [ ] No `.env`, token, credential, or auth files are tracked.
- [ ] No private recordings or transcripts are tracked.
- [ ] No personal replacement dictionary is tracked.
- [ ] No local startup shortcut or machine-specific launcher is tracked.
- [ ] `config/local/`, `_drafts/`, logs, audio, and generated local reports are
  untracked or ignored.

## Content Review

- [ ] README describes the project accurately.
- [ ] README does not claim features that are not implemented.
- [ ] README and release notes state that `v0.1.0` is Codex Desktop first.
- [ ] Browser/ChatGPT/Cursor profiles are described only as future work.
- [ ] Public examples use synthetic data.
- [ ] Screenshots/videos, if any, contain no private chats.
- [ ] License is present.
- [ ] Security/private data policy is present.
- [ ] `docs/release-notes-v0.1.0.md` lists known limitations and rollback path.

## Technical Review

- [ ] `python -m compileall src tests` passes.
- [ ] Unit tests pass.
- [ ] `python -m ruff check src tests` passes.
- [ ] The CLI help command runs.
- [ ] `scripts\smoke.ps1 -BypassProxyForPipAudit` passes, or any skipped step is
  explicitly documented.
- [ ] `docs\codex-profile-checklist.md` has been run against Codex Desktop, or
  unverified live items are listed before release.
- [ ] GitHub Actions CI is green on `main`.

## GitHub Release

- [ ] Dmitrii confirms the exact tag: `v0.1.0`.
- [ ] Dmitrii confirms the GitHub release title and notes.
- [ ] No tag is pushed before explicit confirmation.
- [ ] No GitHub release is created before explicit confirmation.
