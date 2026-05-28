# Architecture

## Initial Architecture

```text
Input Layer
  - global keyboard hotkeys
  - Xbox-compatible controller events
  - optional tray menu

Audio Layer
  - microphone selection
  - push-to-talk recording
  - optional silence trim / VAD

Speech Layer
  - local faster-whisper model
  - model/device/compute-type config

Command Layer
  - text cleanup
  - replacement dictionary
  - voice command detection
  - app profile routing

Output Layer
  - clipboard write
  - SendInput paste
  - Enter / Backspace / cursor keys / mouse wheel / chat navigation actions
  - optional screen-aware chat selection
  - logs and tray status
```

## Configuration Model

Public code must not assume Dmitrii's local paths. Runtime behavior should be
driven by profile files:

- app profile: hotkeys, controller mappings, actions;
- speech profile: model, device, compute type, language;
- text profile: replacements, trash phrases, send commands;
- privacy profile: logging and redaction settings.

## Public API Boundary

The first stable boundary should be a small action model:

```text
dictate_paste
dictate_clipboard
enter
backspace
space
chat_next
chat_previous
cursor_left
cursor_right
cursor_up
cursor_down
focus_chat_list
focus_message_pane
scroll_up
scroll_down
ctrl_tab
ctrl_shift_tab
paste_clipboard
copy_text
```

Controller, keyboard, and voice command inputs should map into this action
model. Output backends then execute actions against the active desktop window.

High-level actions such as `dictate_paste`, `chat_next`, `chat_previous`,
`cursor_left`, `focus_message_pane`, and `scroll_down` should stay separate from
low-level keyboard chords, mouse moves, clicks, or mouse wheel events. App
profiles can choose how to execute those semantic actions for Codex, ChatGPT,
Cursor, browsers, and editors without changing the controller mapping. A Codex
profile may focus the message input before recording for `dictate_paste`, then
paste into that focused input after transcription.

## Screen-Aware Chat Navigation

Screen-aware navigation is allowed only as a conservative app-specific backend.
The controller should still emit `chat_next` and `chat_previous`; a Codex backend
may then inspect the active window, find chat-list items, and click the next or
previous item if confidence is high enough.

The first implementation path is Windows UI Automation through an optional
`screen` extra. UI Automation control types expose semantic roles such as list
items, and pywinauto's UIA backend can enumerate descendants by `control_type`.
If UIA is unavailable, the active window is not Codex, no active chat is found,
or confidence is below the threshold, the backend must not click. It should
return the original semantic action so a safer keyboard fallback can run.

Default logs for this backend must not include chat names or message content.
Allowed logs are technical status, action names, item counts, confidence values,
and redacted coordinates.

## Risks

- Windows global input APIs are fragile and may require fallbacks.
- Controller indices differ across devices.
- Speech models are large and may be hard to package.
- Any logging of dictated text can leak sensitive information.
- Public examples can accidentally expose private workflows if not sanitized.
