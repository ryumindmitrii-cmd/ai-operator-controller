# Roadmap

For the active implementation checklist and milestone acceptance criteria, use
`docs/development-plan.md`. This file is the shorter public phase overview.

## Phase 0: Public Scaffold

- [x] Create clean project directory.
- [x] Add README, license, agent rules, and docs.
- [x] Add safe example config files.
- [x] Add first public-release checklist.
- [x] Initialize git locally.
- [x] Publish public GitHub repository.
- [x] Add GitHub Actions CI for lint and tests.

## Phase 1: Sanitize and Migrate Prototype

- [ ] Move core dictation loop from the private prototype into package modules.
- [ ] Replace hard-coded launch scripts with config profiles.
- [ ] Move private replacements into ignored local config.
- [ ] Keep a safe public example replacement file.
- [x] Add tests for text cleanup and action mapping.
- [x] Add preview dictation runtime command with transcript input.
- [x] Add private learning candidate format and safety boundary.
- [ ] Add a local Windows run command.

## Phase 2: Usable Windows MVP

- [ ] Global hotkeys: paste and clipboard modes.
- [x] Xbox controller mapping with semantic chat and cursor actions.
- [x] Physical controller dry-run listener.
- [ ] SendInput output backend.
- [ ] Tray indicator.
- [ ] Validated model/device config using `large-v3` as the local quality
  default and requiring faster models to be explicit user overrides.
- [ ] Installer/startup docs.
- [ ] Manual test checklist for Codex Desktop.

## Phase 3: Public GitHub Release

- [ ] Confirm no secrets or private logs are tracked.
- [ ] Add screenshots or a short demo GIF without personal data.
- [x] Add GitHub Actions for lint/test.
- [x] Create public GitHub repo.
- [x] Push first public commits.
- [ ] Add release notes for `v0.1.0`.

## Later

- Toggle mode for long dictation.
- Per-app profile auto-detection.
- Voice command grammar.
- Local private learning extractor and review CLI.
- Cloud transcription as opt-in provider.
- Native Windows tray/installer.
- macOS/Linux support if demand exists.
