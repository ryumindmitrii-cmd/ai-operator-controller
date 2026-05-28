# Public Release Checklist

Use this before making the first public GitHub repository.

## Repository Hygiene

- [ ] `git status` shows only intentional files.
- [ ] `.gitignore` excludes virtualenvs, logs, audio, transcripts, secrets, and local configs.
- [ ] No `.env`, token, credential, or auth files are tracked.
- [ ] No private recordings or transcripts are tracked.
- [ ] No personal replacement dictionary is tracked.
- [ ] No local startup shortcut or machine-specific launcher is tracked.

## Content Review

- [ ] README describes the project accurately.
- [ ] README does not claim features that are not implemented.
- [ ] Public examples use synthetic data.
- [ ] Screenshots/videos, if any, contain no private chats.
- [ ] License is present.
- [ ] Security/private data policy is present.

## Technical Review

- [ ] `python -m compileall src tests` passes.
- [ ] Unit tests pass.
- [ ] The CLI help command runs.
- [ ] Windows manual smoke test is documented.

## GitHub Publishing

- [ ] Dmitrii confirms repository name.
- [ ] Dmitrii confirms public visibility.
- [ ] Dmitrii confirms license.
- [ ] Dmitrii confirms GitHub account/organization.
- [ ] No push is performed before explicit confirmation.

