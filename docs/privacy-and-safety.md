# Privacy and Safety

## Default Privacy Position

AI Operator Controller should be local-first:

- audio is recorded locally;
- speech recognition runs locally by default;
- dictated text is not sent to a server by default;
- logs avoid raw transcripts unless explicitly enabled;
- private dictionaries and personal commands are ignored by git.

## Do Not Commit

- `.env` files;
- API keys;
- OAuth tokens;
- real recordings;
- transcripts;
- raw chat exports;
- learning candidate files with private source text;
- private replacement dictionaries;
- personal chat logs;
- screenshots with private content;
- local startup shortcuts;
- machine-specific absolute paths.

## Logging Policy

Default logs should include:

- status transitions;
- action names;
- model/device metadata;
- dictation confidence levels and non-content quality reasons;
- learning candidate counts, candidate types, and redacted source references;
- non-sensitive errors.

Default logs should not include:

- raw dictated text;
- cleaned or polished dictated text;
- raw learning source text;
- full clipboard content;
- message bodies;
- access tokens;
- local user-specific paths unless needed for debugging and clearly redacted.

## Dictation Quality Gate

Automatic Enter/Send is a separate permission from recognizing a trailing voice
command such as "send". When confidence is low, dictated text is long, or local
postprocessing changed the text heavily, the runtime should leave text for manual
review instead of sending it. Quality reasons are safe to log only when they do
not include the dictated content itself.

## Private Learning Pipeline

Learning candidates may improve local hotwords, replacements, punctuation hints,
and assistant guard rules, but raw source material must not be committed. Store
only reviewed candidate metadata and structured payloads. Keep private domains
separated by project profile so that one context does not silently affect
another.

## Public Demo Rule

Use synthetic text and a clean test window for screenshots or videos.
