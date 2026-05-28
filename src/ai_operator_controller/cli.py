from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-operator-controller",
        description="Local-first voice and gamepad control layer for AI workspaces.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["doctor"],
        help="Optional command. The scaffold currently supports only 'doctor'.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "doctor":
        print("AI Operator Controller scaffold is installed.")
        print("Next step: migrate the private prototype through docs/migration-from-local-dictation.md")
        return 0

    parser.print_help()
    return 0

