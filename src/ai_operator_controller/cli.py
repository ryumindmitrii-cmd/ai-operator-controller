from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import __version__
from .audio_recorder import AudioRecorderError, record_microphone_once, record_microphone_to_wav
from .config import ProfileValidationError, load_profile, validate_profile
from .executor import dry_run_action
from .gamepad import GamepadActionResult, GamepadActionRuntime, bindings_from_profile
from .gamepad_listener import PygameGamepadReader, listen_gamepad_dry_run
from .runtime import DICTATION_ACTION_TARGETS, StaticTranscriptProvider, run_dictation_once
from .speech import (
    SpeechConfigError,
    SpeechRecognitionError,
    load_speech_config,
    transcribe_audio_file,
)
from .text_polish import polish_text
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
        help=(
            "Text for 'clean-text'/'polish-text' or transcript text for "
            "'dictate-once'. Reads stdin when omitted."
        ),
    )
    parser.add_argument(
        "--dictation-action",
        choices=sorted(DICTATION_ACTION_TARGETS),
        default="dictate_paste",
        help="Dictation action for the 'dictate-once' command.",
    )
    parser.add_argument(
        "--polish",
        action="store_true",
        help="Apply local deterministic punctuation polish after text cleanup.",
    )
    parser.add_argument(
        "--transcription-confidence",
        type=float,
        help="Optional 0..1 recognition confidence for dictation quality preview.",
    )
    parser.add_argument(
        "--review-long-text-chars",
        type=int,
        default=240,
        help="Require manual review before auto-send when dictated text is longer.",
    )
    parser.add_argument(
        "--max-postprocess-change-ratio",
        type=float,
        default=0.25,
        help="Require manual review before auto-send when polishing changes text too much.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Required for preview-only desktop listeners that must not send real input.",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=2.0,
        help="Recording duration in seconds for the 'record-once' command.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Audio sample rate for the 'record-once' command.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=1,
        help="Audio channel count for the 'record-once' command.",
    )
    parser.add_argument(
        "--mic-device",
        type=int,
        help="Optional microphone device index for the 'record-once' command.",
    )
    parser.add_argument(
        "--speech-profile",
        type=Path,
        default=Path("config/examples/speech.local-quality.example.json"),
        help="Speech profile for the 'transcribe-file' command.",
    )
    parser.add_argument(
        "--audio-file",
        type=Path,
        help="Audio file for the 'transcribe-file' command.",
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow faster-whisper to download a missing model for 'transcribe-file'.",
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
            "polish-text",
            "dictate-once",
            "dictate-run",
            "record-once",
            "transcribe-file",
            "listen-gamepad",
        ],
        help=(
            "Optional command. Use 'doctor', 'plan-action', 'simulate-gamepad', "
            "'clean-text', 'polish-text', 'dictate-once', 'dictate-run', 'record-once', "
            "'transcribe-file', or 'listen-gamepad'."
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

    if args.command == "polish-text":
        try:
            text = polish_text(_read_text_input(args.text))
        except ValueError as exc:
            print(f"Text polish failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: text-polish")
        print("Text:")
        print(text)
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
        print(f"Auto-send: {'yes' if result.quality.send_allowed else 'no'}")
        print(f"Review required: {'yes' if result.quality.review_required else 'no'}")
        print(f"Quality confidence: {result.quality.confidence}")
        quality_reasons = ", ".join(result.quality.reasons) if result.quality.reasons else "none"
        print(f"Quality reasons: {quality_reasons}")
        print("Text:")
        print(result.text)
        print("Dry-run output:")
        for event in result.output_events:
            print(event.describe())
        return 0

    if args.command == "dictate-run":
        try:
            result, audio_summary, transcription = _dictate_run(args)
        except (
            OSError,
            ValueError,
            json.JSONDecodeError,
            AudioRecorderError,
            SpeechConfigError,
            SpeechRecognitionError,
        ) as exc:
            print(f"Dictation runtime failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: dictate-run")
        print("Dry-run: yes")
        print("Saved audio: no")
        print("Source: microphone")
        print(f"Audio duration: {audio_summary.duration_seconds:.3f}s")
        print(f"Audio frames: {audio_summary.frame_count}")
        print(f"Audio RMS: {audio_summary.rms:.6f}")
        print(f"Audio peak: {audio_summary.peak_abs:.6f}")
        print(f"Transcription model: {transcription.model}")
        print(f"Transcription device: {transcription.device}")
        print(f"Transcription compute type: {transcription.compute_type}")
        print(f"Transcription VAD filter: {'enabled' if transcription.vad_filter else 'disabled'}")
        print(f"Transcription fallback used: {'yes' if transcription.used_fallback else 'no'}")
        print(f"Transcription language: {transcription.language or 'unknown'}")
        if transcription.language_probability is None:
            print("Transcription language probability: unknown")
        else:
            print(f"Transcription language probability: {transcription.language_probability:.3f}")
        print(f"Transcription segments: {transcription.segment_count}")
        print(f"Action: {result.action_name}")
        print(f"Output target: {result.output_target}")
        print(f"Should send: {'yes' if result.should_send else 'no'}")
        print(f"Auto-send: {'yes' if result.quality.send_allowed else 'no'}")
        print(f"Review required: {'yes' if result.quality.review_required else 'no'}")
        print(f"Quality confidence: {result.quality.confidence}")
        quality_reasons = ", ".join(result.quality.reasons) if result.quality.reasons else "none"
        print(f"Quality reasons: {quality_reasons}")
        print("Text:")
        print(result.text)
        print("Dry-run output:")
        for event in result.output_events:
            print(event.describe())
        return 0

    if args.command == "record-once":
        try:
            result = _record_once(args)
        except (AudioRecorderError, ValueError) as exc:
            print(f"Record preview failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: record-once")
        print("Dry-run: yes")
        print("Saved file: no")
        print(f"Duration: {result.duration_seconds:.3f}s")
        print(f"Sample rate: {result.sample_rate} Hz")
        print(f"Channels: {result.channel_count}")
        print(f"Frames: {result.frame_count}")
        print(f"Dtype: {result.dtype}")
        print(f"RMS: {result.rms:.6f}")
        print(f"Peak: {result.peak_abs:.6f}")
        return 0

    if args.command == "transcribe-file":
        try:
            result = _transcribe_file(args)
        except (OSError, ValueError, SpeechConfigError, SpeechRecognitionError) as exc:
            print(f"Transcription preview failed: {exc}", file=sys.stderr)
            return 2

        print("Mode: transcribe-file")
        print("Dry-run: yes")
        print("Saved file: no")
        print(f"Model: {result.model}")
        print(f"Device: {result.device}")
        print(f"Compute type: {result.compute_type}")
        print(f"VAD filter: {'enabled' if result.vad_filter else 'disabled'}")
        print(f"Fallback used: {'yes' if result.used_fallback else 'no'}")
        print(f"Model download: {'enabled' if args.allow_model_download else 'disabled'}")
        print(f"Language: {result.language or 'unknown'}")
        if result.language_probability is None:
            print("Language probability: unknown")
        else:
            print(f"Language probability: {result.language_probability:.3f}")
        if result.duration_seconds is None:
            print("Duration: unknown")
        else:
            print(f"Duration: {result.duration_seconds:.3f}s")
        print(f"Segments: {result.segment_count}")
        print("Text:")
        print(result.text)
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
    cleaned = clean_dictation(text, rules)
    if not args.polish:
        return cleaned
    return CleanedDictation(text=polish_text(cleaned.text), should_send=cleaned.should_send)


def _dictate_once(args: argparse.Namespace):
    rules = load_text_rules(args.rules) if args.rules is not None else TextRules()
    transcript = _read_text_input(args.text)
    return run_dictation_once(
        args.dictation_action,
        StaticTranscriptProvider(transcript),
        rules=rules,
        polish=args.polish,
        transcription_confidence=args.transcription_confidence,
        review_long_text_chars=args.review_long_text_chars,
        max_postprocess_change_ratio=args.max_postprocess_change_ratio,
    )


def _record_once(args: argparse.Namespace):
    if not args.dry_run:
        raise ValueError("--dry-run is required for record-once")
    return record_microphone_once(
        seconds=args.seconds,
        sample_rate=args.sample_rate,
        channels=args.channels,
        device=args.mic_device,
    )


def _dictate_run(args: argparse.Namespace):
    if not args.dry_run:
        raise ValueError("--dry-run is required for dictate-run")

    speech_config = load_speech_config(args.speech_profile)
    rules = load_text_rules(args.rules) if args.rules is not None else TextRules()

    temp_path = _make_temp_wav_path()
    try:
        audio_summary = record_microphone_to_wav(
            temp_path,
            seconds=args.seconds,
            sample_rate=args.sample_rate,
            channels=args.channels,
            device=args.mic_device,
        )
        transcription = transcribe_audio_file(
            temp_path,
            speech_config,
            local_files_only=not args.allow_model_download,
        )
        result = run_dictation_once(
            args.dictation_action,
            StaticTranscriptProvider(transcription.text),
            rules=rules,
            polish=args.polish,
            transcription_confidence=transcription.language_probability,
            review_long_text_chars=args.review_long_text_chars,
            max_postprocess_change_ratio=args.max_postprocess_change_ratio,
        )
        return result, audio_summary, transcription
    finally:
        temp_path.unlink(missing_ok=True)


def _transcribe_file(args: argparse.Namespace):
    if not args.dry_run:
        raise ValueError("--dry-run is required for transcribe-file")
    if args.audio_file is None:
        raise ValueError("--audio-file is required for transcribe-file")
    config = load_speech_config(args.speech_profile)
    return transcribe_audio_file(
        args.audio_file,
        config,
        local_files_only=not args.allow_model_download,
    )


def _make_temp_wav_path() -> Path:
    handle = tempfile.NamedTemporaryFile(prefix="ai-operator-", suffix=".wav", delete=False)
    path = Path(handle.name)
    handle.close()
    return path


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
