# AI Operator Controller v0.1.0 Release Notes

Status: released.

Release: `v0.1.0` Windows Codex Desktop local preview.
Release date: 2026-06-22.

This release is the first public preview for technically curious Windows users
who want to test a local voice and Xbox-controller control layer for Codex
Desktop. It is not a one-click consumer installer and it is not a general
browser automation profile.

## Scope

Included in `v0.1.0`:

- Windows-first Python package and CLI.
- Local `faster-whisper` speech profile with `large-v3` as the quality default.
- Metadata-only microphone dry-run.
- Local file transcription dry-run.
- Microphone-to-transcript-to-output planning through `dictate-run --dry-run`.
- Explicit Windows paste output through `dictate-run --execute-output`.
- Safe PowerShell setup, smoke, and runtime launcher scripts.
- Read-only `doctor` command for package, audio, speech runtime, CUDA/CPU, and
  gamepad visibility checks.
- Ignored local config bootstrap under `config/local/`.
- Public Codex Desktop controller profile.
- Physical controller dry-run listener.
- Codex profile checklist for manual validation.
- Text cleanup and deterministic local punctuation polish.
- Dictation quality gate that blocks automatic Enter when review is safer.
- Privacy and public-release safeguards for logs, transcripts, recordings,
  local paths, and private dictionaries.

Not included in `v0.1.0`:

- Windows installer, tray app, or background autostart.
- ChatGPT browser profile.
- Cursor/browser/editor profiles.
- General gamepad mapper behavior.
- Cloud transcription.
- Automatic login, cookie handling, or account automation.
- Automatic training from chat history or private transcripts.

## Install And First Run

```powershell
git clone https://github.com/ryumindmitrii-cmd/ai-operator-controller.git
cd ai-operator-controller
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-dev.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode doctor
```

For controller dry-run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode gamepad-dry-run -GamepadMaxEvents 20
```

For dictation dry-run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode dictation-dry-run -Seconds 2
```

Real desktop output remains explicit:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-runtime.ps1 -Mode dictation-execute -Seconds 2 -ConfirmExecute
```

Use real output only after focusing a safe scratch window.

## Verification Used Before Tagging

`v0.1.0` was tagged only after these checks were true:

- CI is green on `main`.
- `scripts\smoke.ps1 -BypassProxyForPipAudit` passes.
- `docs\public-release-checklist.md` is complete.
- `docs\codex-profile-checklist.md` has been run against Codex Desktop or the
  unverified items are explicitly listed.
- No private logs, transcripts, recordings, local configs, secrets, or personal
  paths are tracked.

Release evidence from 2026-06-22:

- `scripts\smoke.ps1 -BypassProxyForPipAudit` passed locally.
- The physical controller dry-run listener covered the public Codex mapping
  contract.
- Dmitrii manually confirmed live Codex Desktop controller behavior on the
  maintainer Windows setup.
- GitHub Actions CI passed on the final release commit before tagging.

## Known Limitations

- The public controller runtime is still safest to validate in dry-run mode on
  a new machine before enabling live output.
- Maintainer live Codex Desktop behavior has been manually confirmed, but other
  monitors and Windows scaling settings need their own local checklist run.
- `A` and `X` are documented in the Codex profile, but the public
  `listen-gamepad --dry-run` command still reports `dictate_paste` as a future
  runtime action rather than starting recording.
- Coordinate-based focus behavior can require local tuning under
  `config/local/` on different monitors or Windows scaling settings.
- The current setup expects PowerShell and Python familiarity.
- The speech model may need a large local download unless it is already cached.

## Rollback

If the release is tagged incorrectly:

1. Do not publish additional packages.
2. Delete or mark the GitHub release as draft if it was created.
3. Move the tag only after a corrected commit is verified, or create a patch tag
   such as `v0.1.1`.
