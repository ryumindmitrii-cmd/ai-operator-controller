from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ProfileValidationError, load_profile, validate_profile
from .executor import dry_run_action


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-operator-controller",
        description="Local-first voice and gamepad control layer for AI workspaces.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument(
        "--profile",
        type=Path,
        help="Validate an app profile when running the 'doctor' command.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["doctor", "plan-action"],
        help="Optional command. Use 'doctor' or 'plan-action'.",
    )
    parser.add_argument(
        "action_name",
        nargs="?",
        help="Action name to plan when running the 'plan-action' command.",
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
        if args.profile is not None:
            try:
                profile = load_profile(args.profile)
                result = validate_profile(profile, source=args.profile)
            except ProfileValidationError as exc:
                print(f"Profile validation failed: {exc}", file=sys.stderr)
                return 2

            print(f"Profile: {result.profile_name}")
            print(f"Actions: valid ({len(result.actions)})")
            print(
                "Gamepad mapping: valid "
                f"({result.button_count} buttons, {result.axis_count} axes, {result.hat_count} hats)"
            )
            print(f"Focus targets: valid ({result.focus_target_count})")
            print("Private/local markers: none detected")
        print("Next step: migrate the private prototype through docs/migration-from-local-dictation.md")
        return 0

    if args.command == "plan-action":
        if args.action_name is None:
            print("Action planning failed: missing action name", file=sys.stderr)
            return 2
        try:
            events = dry_run_action(args.action_name)
        except ValueError as exc:
            print(f"Action planning failed for {args.action_name}: {exc}", file=sys.stderr)
            return 2

        print(f"Action: {args.action_name}")
        print("Mode: dry-run")
        for event in events:
            print(event.describe())
        return 0

    parser.print_help()
    return 0
