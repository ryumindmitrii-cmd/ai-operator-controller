# Product Brief

## Problem

AI-heavy work often requires rapid switching between chats, writing long prompts,
editing text, and sending messages. Traditional keyboard-first workflows are
slow and physically repetitive, especially when the user is thinking aloud.

## Recommended Direction

Build a small local control layer for AI workspaces. The project should combine:

- local push-to-talk dictation;
- controller mappings for high-frequency actions;
- text normalization and voice commands;
- app profiles for Codex, ChatGPT, Cursor, browsers, and editors.

The differentiator is not speech-to-text alone. The differentiator is ergonomic
control of AI workspaces: dictate, paste, send, delete, and switch chats from a
controller while keeping privacy local.

## Target Users

- Developers and researchers who spend hours in AI coding/chat tools.
- Power users who prefer voice capture for long prompts.
- Users with typing strain who need a pragmatic local workflow.
- People building custom desktop AI workstations.

## Success Criteria

- A user can install the tool on Windows and use it in Codex without editing
  source code.
- The default profile supports dictation, clipboard-only mode, Enter,
  Backspace, and recent-chat navigation.
- Private voice audio and transcripts stay local by default.
- Public examples are clean and contain no private paths or personal data.

## Key Assumptions to Validate

- Users want app-specific AI workflow controls, not just generic dictation.
- Python is acceptable for the first open-source version despite packaging
  friction on Windows.
- Controller mappings are valuable enough to differentiate the project from
  existing dictation apps.
- Local GPU transcription is a meaningful selling point for power users.

