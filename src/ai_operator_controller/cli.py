from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import ProfileValidationError, load_profile, validate_profile
from .executor import dry_run_action
from .gamepad import GamepadActionResult, GamepadActionRuntime, bindings_from_profile
from .gamepad_listener import PygameGamepadReader, listen_gamepad_dry_run
from .runtime import DICTATION_ACTION_TARGETS, StaticTranscriptProvider, run_dictation_once
from .text_rules import CleanedDictation, TextRules, clean_dictation, load_text_rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-operator-controller",
        description="Local-first voice and gamepad control layer for AI workspaces.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument(
        "--profile",
        type=Path,
        help="Validate or simulate against an app profile.",
    )
    parser.add_argument(
        "--button",
        nargs=2,
        metavar=("NAME", "STATE"),
        help="Simulate a gamepad button, for example: --button b down.",
    )
    parser.add_argument(
        "--axis",
        nargs=2,
        metavar=("NAME", "VALUE"),
        help="Simulate a gamepad axis, for example: --axis right_stick_x 0.8.",
    )
    parser.add_argument(
        "--hat",
        nargs=3,
        metavar=("NAME", "X", "Y"),
        help="Simulate a gamepad hat, for example: --hat dpad 0 -1.",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        help="Text cleanup rules file for the 'clean-text' command.",
    )
    parser.add_argument(
        "--text",
        help="Text for 'clean-text' or transcript text for 'dictate-once'. Reads stdin when omitted.",
    )
    parser.add_argument(
        "--dictation-action",
        choices=sorted(DICTATION_ACTION_TARGETS),
        default="dictate_paste",
        help="Dictation action for the 'dictate-once' command.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for preview-only desktop listeners that must not send real input.",
    )
    parser.add_argument(
        "--gamepad-index",
        type=int,
        help="Override the gamepad device index from the selected profile.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        help="Stop a listener after this many emitted actions.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.03,
        help="Polling interval in seconds for physical gamepad listeners.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=[
            "doctor",
            "plan-action",
            "simulate-gamepad",
            "clean-text",
            "dictate-once",
            "listen-gamepad",
        ],
        help=(
            "Optional command. Use 'doctor', 'plan-action', 'simulate-gamepad', "
            "'clean-text', 'dictate-once', or 'listen-gamepad'."
        ),
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

    if args.command == "clean-text":
        try:
            result = _clean_text(args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Text cleanup failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: text-cleanup")
        print(f"Should send: {'yes' if result.should_send else 'no'}")
        print("Text:")
        print(result.text)
        return 0

    if args.command == "dictate-once":
        try:
            result = _dictate_once(args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Dictation preview failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: dictate-once")
        print("Source: transcript")
        print(f"Action: {result.action_name}")
        print(f"Output target: {result.output_target}")
        print(f"Should send: {'yes' if result.should_send else 'no'}")
        print("Text:")
        print(result.text)
        print("Dry-run output:")
        for event in result.output_events:
            print(event.describe())
        return 0

    if args.command == "simulate-gamepad":
        try:
            result = _simulate_gamepad(args)
        except (ProfileValidationError, ValueError) as exc:
            print(f"Gamepad simulation failed: {exc}", file=sys.stderr)
            return 2

        if result is None:
            print("Action: none")
            return 0

        print(f"Action: {result.action_name}")
        print("Mode: dry-run")
        if result.unsupported_reason is not None:
            print(f"Output: unsupported ({result.unsupported_reason})")
            return 0
        for event in result.output_events:
            print(event.describe())
        return 0

    if args.command == "listen-gamepad":
        try:
            return _listen_gamepad(args)
        except (ProfileValidationError, RuntimeError, ValueError) as exc:
            print(f"Gamepad listener failed: {exc}", file=sys.stderr)
            return 2

    parser.print_help()
    return 0


def _clean_text(args: argparse.Namespace) -> CleanedDictation:
    rules = load_text_rules(args.rules) if args.rules is not None else TextRules()
    text = _read_text_input(args.text)
    return clean_dictation(text, rules)


def _dictate_once(args: argparse.Namespace):
    rules = load_text_rules(args.rules) if args.rules is not None else TextRules()
    transcript = _read_text_input(args.text)
    return run_dictation_once(
        args.dictation_action,
        StaticTranscriptProvider(transcript),
        rules=rules,
    )


def _read_text_input(argument_text: str | None) -> str:
    if argument_text is not None:
        return argument_text

    if sys.stdin.isatty():
        raise ValueError("provide --text or pipe text on stdin")

    text = sys.stdin.read()
    if text == "":
        raise ValueError("provide --text or pipe text on stdin")
    return text


def _simulate_gamepad(args: argparse.Namespace) -> GamepadActionResult | None:
    if args.profile is None:
        raise ValueError("--profile is required for simulate-gamepad")

    provided_inputs = [
        args.button is not None,
        args.axis is not None,
        args.hat is not None,
    ]
    if sum(provided_inputs) != 1:
        raise ValueError("provide exactly one of --button, --axis, or --hat")

    profile = load_profile(args.profile)
    validate_profile(profile, source=args.profile)
    runtime = GamepadActionRuntime(bindings_from_profile(profile))

    if args.button is not None:
        name, state = args.button
        pressed = _parse_button_state(state)
        print(f"Input: button {name} {state}")
        try:
            return runtime.update_button(name, pressed, now=0.0)
        except KeyError as exc:
            raise ValueError(f"unknown gamepad button: {name}") from exc

    if args.axis is not None:
        name, value = args.axis
        axis_value = float(value)
        print(f"Input: axis {name} {axis_value:g}")
        try:
            return runtime.update_axis(name, axis_value, now=0.0)
        except KeyError as exc:
            raise ValueError(f"unknown gamepad axis: {name}") from exc

    name, x_value, y_value = args.hat
    hat_value = (int(x_value), int(y_value))
    print(f"Input: hat {name} {hat_value[0]} {hat_value[1]}")
    try:
        return runtime.update_hat(name, hat_value, now=0.0)
    except KeyError as exc:
        raise ValueError(f"unknown gamepad hat: {name}") from exc


def _listen_gamepad(args: argparse.Namespace) -> int:
    if not args.dry_run:
        raise ValueError("--dry-run is required for listen-gamepad")
    if args.profile is None:
        raise ValueError("--profile is required for listen-gamepad")

    profile = load_profile(args.profile)
    validate_profile(profile, source=args.profile)
    bindings = bindings_from_profile(profile)
    gamepad_index = args.gamepad_index
    if gamepad_index is None:
        gamepad_index = int(profile["gamepad"].get("index", 0))

    reader = PygameGamepadReader(device_index=gamepad_index)
    print(f"Controller: {reader.controller_name}")
    print("Mode: dry-run")
    print("Listening for mapped gamepad actions. Press Ctrl+C to stop.")

    count = listen_gamepad_dry_run(
        bindings,
        reader,
        max_events=args.max_events,
        poll_interval_seconds=args.poll_interval,
        emit=_print_polled_gamepad_action,
    )
    print(f"Stopped after {count} action(s).")
    return 0


def _print_polled_gamepad_action(action) -> None:
    print(action.describe_input())
    print(f"Action: {action.result.action_name}")
    if action.result.unsupported_reason is not None:
        print(f"Output: unsupported ({action.result.unsupported_reason})")
        return
    for event in action.result.output_events:
        print(event.describe())


def _parse_button_state(state: str) -> bool:
    if state == "down":
        return True
    if state == "up":
        return False
    raise ValueError("button state must be 'down' or 'up'")
