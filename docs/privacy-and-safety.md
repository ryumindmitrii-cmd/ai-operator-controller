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
- non-sensitive errors.

Default logs should not include:

- raw dictated text;
- full clipboard content;
- message bodies;
- access tokens;
- local user-specific paths unless needed for debugging and clearly redacted.

## Public Demo Rule

Use synthetic text and a clean test window for screenshots or videos.

