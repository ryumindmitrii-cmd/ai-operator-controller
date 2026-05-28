# ADR-001: Project Scope and Public Positioning

## Status

Accepted

## Date

2026-05-28

## Context

The private prototype started as a personal local dictation tool for Codex:
push-to-talk speech recognition, Xbox controller mappings, text cleanup, tray
status, and Windows paste/keyboard actions.

The open-source landscape already has several dictation tools and several
gamepad-to-keyboard mappers. Publishing another generic dictation app would be
undifferentiated.

## Decision

Position the public project as a local-first control layer for AI workspaces,
not as a generic dictation app.

The first supported workflow is:

- dictate into AI chats;
- send or keep text in clipboard;
- switch recent chats;
- edit with Backspace;
- press Enter;
- keep transcription local by default;
- configure app-specific profiles.

## Alternatives Considered

### Generic Dictation App

Pros:
- Easier to explain.
- Larger apparent market.

Cons:
- Crowded space.
- Less connected to the actual user pain.
- Harder to differentiate.

Rejected for initial positioning.

### Generic Gamepad Mapper

Pros:
- Simple mental model.
- Many possible use cases.

Cons:
- Already served by mature tools.
- Does not capture voice/text cleanup workflows.

Rejected for initial positioning.

### AI Workspace Controller

Pros:
- Matches the working prototype.
- Distinct from plain dictation and plain controller mapping.
- Useful for Codex/ChatGPT/Cursor power users.

Cons:
- Smaller initial audience.
- Requires careful examples to explain the value.

Accepted.

## Consequences

- README and docs should emphasize AI workflow control.
- Public examples should target Codex/ChatGPT-style workflows.
- The project should keep clear boundaries and avoid becoming a broad desktop
  automation framework.

