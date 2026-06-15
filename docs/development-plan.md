# Development Plan

Last updated: 2026-06-15.

This is the working product and implementation plan for AI Operator Controller.
It is intentionally more operational than `docs/roadmap.md`: future maintainers
and coding agents should use it to choose the next patch, close checkboxes, and
avoid drifting into low-impact features.

## Product Thesis

AI Operator Controller should become a Windows-first, local-first control layer
for long AI workspace sessions. The user should be able to dictate, edit,
navigate chats, scroll, and send messages with voice plus an Xbox-compatible
controller, while keeping audio, transcripts, logs, and personal dictionaries
local by default.

The near-term product is not a general gamepad mapper, not a cloud dictation
service, and not a broad agent framework. The first useful version should make
Codex and ChatGPT sessions less keyboard-bound for power users and accessibility
use cases.

## Current Status

- [x] Public GitHub repository exists.
- [x] MIT license and project docs exist.
- [x] CI runs compile, lint, and tests on `main`.
- [x] Public examples avoid private paths and personal data.
- [x] Text cleanup rules support replacements, filler removal, and send command
  detection.
- [x] Local deterministic text polish exists.
- [x] Dictation quality gate separates requested send from allowed auto-send.
- [x] Xbox-compatible public Codex profile covers dictation, cursor movement,
  scrolling, mouse clicks, panel toggles, and chat navigation actions.
- [x] Physical controller dry-run listener exists.
- [x] Private learning candidate format and validator exist.
- [x] GitHub Discussions are enabled and seeded.
- [x] Public package can record a short microphone sample for metadata-only
  `record-once --dry-run` diagnostics.
- [x] Reproducible local setup and smoke scripts exist for venv creation, CLI
  dry-runs, tests, lint, compile checks, privacy/security scans, and optional
  microphone metadata smoke tests.
- [x] Read-only `doctor` reports package, Python/platform, audio inputs,
  selected microphone, speech profile, speech runtime, CUDA/compute-type status,
  gamepad visibility, and profile validation without recording audio or sending
  desktop input.
- [x] Public package has a test-covered `faster-whisper` config/backend wrapper
  and `transcribe-file --dry-run` command for explicit local audio files.
- [x] Real local `faster-whisper` model smoke test runs with cached `large-v3` on
  CUDA against synthetic silence; VAD returns an empty transcript instead of
  prompt text.
- [x] Public package can run microphone-to-transcript-to-output planning through
  `dictate-run --dry-run` without touching the clipboard or keyboard.
- [ ] Public package does not yet run push-to-talk hotkey/controller dictation.
- [x] Public package can send explicit Windows paste output through
  `dictate-run --execute-output`.
- [ ] There is no one-command installer or startup setup.

## North-Star User Journey

A new Windows user should be able to:

1. Clone or download the project.
2. Run a setup command.
3. Connect an Xbox-compatible controller.
4. Run a doctor command that validates audio, speech backend, controller, and
   app profile.
5. Open Codex or ChatGPT.
6. Press `A`, dictate text locally, and paste it into the message box.
7. Use the controller to edit, scroll, switch chat targets, and send.
8. Keep private logs, recordings, transcripts, and dictionaries outside git.

Time-to-first-use target for `v0.1.0`: 10-15 minutes on a prepared Windows
machine.

## Product Metrics

Use practical proof instead of social metrics until the product is installable:

- Time from clean checkout to `doctor` success.
- Time from checkout to first local dictated paste.
- Number of manual steps requiring technical judgment.
- Number of private files a user must create or edit by hand.
- End-to-end success on at least two Windows machines.
- No private data in public git history.

## Milestone 1: Public Runtime Slice

Goal: move the minimum real runtime out of the private prototype and into the
public package without copying private data.

- [x] Add public microphone recorder module.
  - Acceptance: can record a short local sample through a testable interface.
  - Verification: unit tests for audio buffer handling; manual metadata-only
    `record-once --dry-run` on Windows.
- [x] Add public `faster-whisper` speech backend wrapper.
  - Acceptance: backend accepts model/device config and returns transcript text
    plus confidence metadata when available.
  - Verification: mocked backend tests plus manual local model smoke test with
    cached `large-v3` on synthetic silence.
- [x] Add local runtime command for paste and clipboard modes.
  - Acceptance: `dictate-run` or equivalent can record, transcribe, clean,
    polish, quality-check, and write planned output events.
  - Verification: tests for pipeline composition and one manual local dry run.
- [x] Add Windows output backend behind an explicit runtime flag.
  - Acceptance: real clipboard/paste/Enter execution is impossible from dry-run
    commands and only enabled by the runtime command.
  - Verification: tests for backend selection and manual paste into a clean test
    window.
  - Status: `dictate-run --execute-output` and metadata-only event recording are
    implemented and test-covered. Manual Notepad live smoke verified on
    2026-06-15 with an explicit Fanvil microphone device.
- [x] Keep logs metadata-only by default.
  - Acceptance: default logs contain action names, lengths, confidence, and
    technical state, but not dictated text or clipboard contents.
  - Verification: execute-output CLI output hides dictated text and reports only
    length, quality, metadata, and output event names.

Checkpoint:

- [x] Public runtime can perform one local dictated paste on the maintainer's
  Windows machine.
- [ ] Tests pass: `python -m pytest`.
- [ ] Lint passes: `python -m ruff check src tests`.
- [ ] Public scan finds no private paths, email, tokens, logs, transcripts, or
  recordings.

## Milestone 2: Windows Setup and Doctor

Goal: make the first install less dependent on Python knowledge.

- [ ] Add PowerShell setup script.
  - Acceptance: creates venv, installs package, and prints next commands.
  - Verification: run on a clean checkout.
- [x] Add `doctor` checks for runtime prerequisites.
  - Acceptance: reports Python, package import, audio device availability,
    controller visibility, speech profile, and CUDA/CPU fallback status.
  - Verification: tests for report formatting plus manual run on 2026-06-15.
- [ ] Add local config bootstrap.
  - Acceptance: creates ignored local config from public examples without
    overwriting existing private files.
  - Verification: tests for idempotent file creation.
- [ ] Add Windows startup/tray guidance.
  - Acceptance: user can start the runtime without editing source code.
  - Verification: manual checklist.

Checkpoint:

- [ ] A second Windows machine can reach `doctor` success in 10-15 minutes.
- [ ] Setup docs match actual command output.

## Milestone 3: Codex and ChatGPT App Profiles

Goal: make controller behavior reliable in real AI workspaces.

- [ ] Harden Codex profile as the first supported profile.
  - Acceptance: `A`, `X`, `B`, `LB`, `RB`, `LT`, `RT`, sticks, D-pad, `Y`, and
    Menu/Start work as documented.
  - Verification: manual Codex checklist and dry-run tests.
- [ ] Add ChatGPT browser profile.
  - Acceptance: core dictate/edit/scroll/send flow works in Chrome or Edge.
  - Verification: manual browser checklist.
- [ ] Add profile selection docs.
  - Acceptance: user understands which profile to use and how to override local
    coordinates safely.
  - Verification: README/quickstart review.
- [ ] Add profile validation for any new profile fields.
  - Acceptance: invalid actions, unsafe paths, and malformed focus targets fail
    early.
  - Verification: unit tests.

Checkpoint:

- [ ] One Codex session and one ChatGPT browser session can be controlled from a
  controller without editing source code.

## Milestone 4: Private Learning Pipeline

Goal: improve recognition and assistant behavior through reviewed local
candidates, not automatic training on raw chat history.

- [ ] Add local candidate review CLI.
  - Acceptance: validates candidate files and prints approve/reject/edit
    workflow without reading unapproved sources.
  - Verification: unit tests and synthetic example.
- [ ] Add compiler from approved candidates to local runtime files.
  - Acceptance: approved hotwords, replacements, punctuation hints, and assistant
    guards compile into ignored local config.
  - Verification: tests for generated config; no raw source text emitted.
- [ ] Add optional local extractor for explicit source files.
  - Acceptance: extractor requires an explicit source path and produces
    candidates only, never active rules.
  - Verification: tests with synthetic sources; privacy scan.
- [ ] Add per-profile learning docs.
  - Acceptance: users can keep work, university, open-source, and personal
    dictionaries separated.
  - Verification: docs review.

Checkpoint:

- [ ] A synthetic correction can become an approved local hotword/replacement
  without raw text entering git.

## Milestone 5: v0.1.0 Windows Local Preview

Goal: ship something a technically curious Windows user can actually try.

- [ ] Complete public runtime slice.
- [ ] Complete Windows setup and doctor.
- [ ] Complete Codex profile checklist.
- [ ] Add release notes.
- [ ] Add clean demo assets that do not show personal desktop content.
- [ ] Confirm public repository scan is clean.
- [ ] Tag `v0.1.0` only after CI is green.

Release criteria:

- [ ] Fresh install documented.
- [ ] First dictated paste works.
- [ ] Controller basics work.
- [ ] Safety defaults are documented and tested.
- [ ] No private logs, transcripts, recordings, paths, or dictionaries are
  tracked.

## Milestone 6: Public Feedback Loop

Goal: collect useful feedback only after the product is runnable.

- [ ] Open setup-focused GitHub issues.
- [ ] Write an accessibility-focused announcement.
- [ ] Add "known limitations" to README.
- [ ] Ask for feedback from Windows/Codex/ChatGPT power users.
- [ ] Track failures by setup step, not vague impressions.

Do not spend energy on broad promotion before `v0.1.0` can produce a first local
dictated paste for a new user.

## Later Candidates

These are intentionally not next:

- [ ] Native GUI/tray application.
- [ ] Packaged Windows installer.
- [ ] Cursor-specific profile.
- [ ] Per-app auto-detection.
- [ ] Voice command grammar beyond basic text cleanup.
- [ ] Cloud transcription provider as an explicit opt-in.
- [ ] macOS/Linux support.

## Update Discipline

- Close a checkbox only after the acceptance criteria and verification are true.
- When closing a milestone item, add a short note to the relevant PR/commit or
  update this document in the same patch.
- Do not add private paths, raw transcripts, recordings, logs, screenshots, or
  personal dictionaries to prove progress.
- Prefer small patches that leave CI green.
- If the private prototype is used as reference, migrate behavior deliberately
  and sanitize before committing.
