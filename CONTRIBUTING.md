# Contributing

This project is pre-alpha. Contributions are welcome after the first public
release, but the initial phase focuses on extracting and sanitizing the private
prototype.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

## Rules

- Do not add telemetry or network calls without explicit opt-in.
- Do not log raw dictated text by default.
- Keep public examples synthetic.
- Add tests for text cleanup, command routing, and controller mappings.

