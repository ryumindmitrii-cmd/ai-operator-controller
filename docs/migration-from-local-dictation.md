# Migration From Private Prototype

Private prototype path:

```text
<private-prototype-path>
```

## Goal

Move the useful behavior into this repository without publishing personal
state, logs, recordings, local paths, or private replacement dictionaries.

## Source Files to Review

- `ptt_dictation.py`
- `README.md`
- `requirements.txt`
- PowerShell startup/status scripts

## Files Not to Copy Directly

- `.venv/`
- `logs/`
- `__pycache__/`
- `replacements.json`
- desktop shortcuts;
- autostart shortcut;
- machine-specific launcher paths.

## Migration Steps

1. Split the prototype into modules:
   - `audio.py`;
   - `speech.py`;
   - `text_rules.py`;
   - `actions.py`;
   - `gamepad.py`;
   - `hotkeys.py`;
   - `tray.py`;
   - `config.py`.
2. Add unit tests for:
   - replacements;
   - trash phrase filtering;
   - voice send detection;
   - gamepad event to action mapping.
3. Keep Windows integration behind an output backend interface.
4. Add a safe example config.
5. Run public-release checklist before the first commit intended for GitHub.

## Acceptance Criteria

- The migrated code runs from this repository.
- The private prototype can still run independently until replacement is ready.
- No private text, audio, logs, or absolute personal paths are tracked.
