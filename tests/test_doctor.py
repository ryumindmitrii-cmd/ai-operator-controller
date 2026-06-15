from types import SimpleNamespace

from ai_operator_controller.doctor import (
    CheckResult,
    DoctorReport,
    format_doctor_report,
    probe_audio_devices,
    probe_gamepad,
)


class FakeSoundDevice:
    default = SimpleNamespace(device=[1, 4])

    @staticmethod
    def query_devices():
        return [
            {"name": "Output only", "max_input_channels": 0, "default_samplerate": 48000},
            {"name": "Webcam Mic", "max_input_channels": 1, "default_samplerate": 44100},
            {"name": "Desk Mic", "max_input_channels": 2, "default_samplerate": 48000},
        ]


class FakeSoundDeviceWithoutDefault:
    default = SimpleNamespace(device=[None, 4])

    @staticmethod
    def query_devices():
        return [
            {"name": "Desk Mic", "max_input_channels": 2, "default_samplerate": 48000},
        ]


def test_probe_audio_devices_reports_default_and_selected_input():
    check = probe_audio_devices(mic_device=2, sounddevice_module=FakeSoundDevice)

    assert check.status == "ok"
    assert "input devices: 2" in check.detail
    assert "default: 1 Webcam Mic" in check.detail
    assert "selected: 2 Desk Mic" in check.detail


def test_probe_audio_devices_handles_missing_default_input():
    check = probe_audio_devices(mic_device=None, sounddevice_module=FakeSoundDeviceWithoutDefault)

    assert check.status == "ok"
    assert "input devices: 1" in check.detail
    assert "default: unknown" in check.detail
    assert "selected: not specified" in check.detail
    assert check.next_step == (
        "Use --mic-device <INDEX> if Windows has no default input or chooses the wrong mic."
    )


def test_probe_audio_devices_warns_for_missing_selected_input():
    check = probe_audio_devices(mic_device=5, sounddevice_module=FakeSoundDevice)

    assert check.status == "warning"
    assert "selected input 5 not found" in check.detail
    assert check.next_step == "Run doctor without --mic-device or choose a listed input device index."


def test_probe_gamepad_reports_connected_controller():
    class FakeJoystick:
        def __init__(self, index):
            assert index == 0

        def get_name(self):
            return "Xbox Controller"

    class FakeJoystickModule:
        def init(self):
            pass

        def quit(self):
            pass

        def get_count(self):
            return 1

        def Joystick(self, index):
            return FakeJoystick(index)

    class FakePygame:
        joystick = FakeJoystickModule()
        event = SimpleNamespace(pump=lambda: None)

        @staticmethod
        def init():
            pass

        @staticmethod
        def quit():
            pass

    check = probe_gamepad(gamepad_index=0, pygame_module=FakePygame)

    assert check.status == "ok"
    assert "detected: 1" in check.detail
    assert "selected: 0 Xbox Controller" in check.detail


def test_format_doctor_report_includes_safe_boundary_and_next_steps():
    report = DoctorReport(
        checks=(
            CheckResult("Package", "ok", "ai-operator-controller 0.1.0"),
            CheckResult(
                "Audio",
                "warning",
                "selected input 5 not found",
                "Run doctor without --mic-device.",
            ),
        ),
        next_steps=("Run record-once --dry-run for metadata-only microphone smoke.",),
    )

    output = "\n".join(format_doctor_report(report))

    assert "AI Operator Controller doctor" in output
    assert "[ok] Package: ai-operator-controller 0.1.0" in output
    assert "[warning] Audio: selected input 5 not found" in output
    assert "Next: Run doctor without --mic-device." in output
    assert "No audio was recorded. No clipboard or keyboard output was sent." in output
    assert "Run record-once --dry-run for metadata-only microphone smoke." in output
