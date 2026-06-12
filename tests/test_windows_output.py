import pytest

from ai_operator_controller.windows_output import WindowsDesktopOutputBackend, WindowsOutputError


class FakeKeyboard:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))


class FailingKeyboard(FakeKeyboard):
    def press(self, key):
        self.events.append(("press", key))
        if key == "KEY_SHIFT":
            raise RuntimeError("press failed")


class FakeMouse:
    def __init__(self):
        self.events = []

    def scroll(self, dx, dy):
        self.events.append(("scroll", dx, dy))

    def click(self, button):
        self.events.append(("click", button))


class FakeKey:
    ctrl = "KEY_CTRL"
    shift = "KEY_SHIFT"
    alt = "KEY_ALT"
    tab = "KEY_TAB"
    enter = "KEY_ENTER"
    backspace = "KEY_BACKSPACE"
    left = "KEY_LEFT"
    right = "KEY_RIGHT"
    up = "KEY_UP"
    down = "KEY_DOWN"
    space = "KEY_SPACE"


class FakeButton:
    left = "BUTTON_LEFT"
    right = "BUTTON_RIGHT"


def test_windows_output_backend_pastes_text_via_clipboard_and_ctrl_v():
    copied = []
    slept = []
    keyboard = FakeKeyboard()
    backend = WindowsDesktopOutputBackend(
        keyboard_controller=keyboard,
        mouse_controller=FakeMouse(),
        key_namespace=FakeKey,
        button_namespace=FakeButton,
        clipboard_copy=copied.append,
        sleep=slept.append,
        paste_delay_seconds=0.2,
    )

    backend.write_text("hello", target="paste")

    assert copied == ["hello"]
    assert keyboard.events == [
        ("press", "KEY_CTRL"),
        ("press", "v"),
        ("release", "v"),
        ("release", "KEY_CTRL"),
    ]
    assert slept == [0.2]


def test_windows_output_backend_clipboard_target_only_copies_text():
    copied = []
    keyboard = FakeKeyboard()
    backend = WindowsDesktopOutputBackend(
        keyboard_controller=keyboard,
        mouse_controller=FakeMouse(),
        key_namespace=FakeKey,
        button_namespace=FakeButton,
        clipboard_copy=copied.append,
        sleep=lambda _seconds: None,
    )

    backend.write_text("clipboard only", target="clipboard")

    assert copied == ["clipboard only"]
    assert keyboard.events == []


def test_windows_output_backend_supports_keyboard_mouse_and_scroll_actions():
    keyboard = FakeKeyboard()
    mouse = FakeMouse()
    backend = WindowsDesktopOutputBackend(
        keyboard_controller=keyboard,
        mouse_controller=mouse,
        key_namespace=FakeKey,
        button_namespace=FakeButton,
        clipboard_copy=lambda _text: None,
        sleep=lambda _seconds: None,
    )

    backend.press_keys(("ctrl", "shift", "tab"))
    backend.scroll(-0.5)
    backend.click_mouse("right")

    assert keyboard.events == [
        ("press", "KEY_CTRL"),
        ("press", "KEY_SHIFT"),
        ("press", "KEY_TAB"),
        ("release", "KEY_TAB"),
        ("release", "KEY_SHIFT"),
        ("release", "KEY_CTRL"),
    ]
    assert mouse.events == [
        ("scroll", 0, -0.5),
        ("click", "BUTTON_RIGHT"),
    ]


def test_windows_output_backend_releases_pressed_keys_after_press_failure():
    keyboard = FailingKeyboard()
    backend = WindowsDesktopOutputBackend(
        keyboard_controller=keyboard,
        mouse_controller=FakeMouse(),
        key_namespace=FakeKey,
        button_namespace=FakeButton,
        clipboard_copy=lambda _text: None,
        sleep=lambda _seconds: None,
    )

    with pytest.raises(RuntimeError, match="press failed"):
        backend.press_keys(("ctrl", "shift", "tab"))

    assert keyboard.events == [
        ("press", "KEY_CTRL"),
        ("press", "KEY_SHIFT"),
        ("release", "KEY_CTRL"),
    ]


def test_windows_output_backend_rejects_unimplemented_focus_targets():
    backend = WindowsDesktopOutputBackend(
        keyboard_controller=FakeKeyboard(),
        mouse_controller=FakeMouse(),
        key_namespace=FakeKey,
        button_namespace=FakeButton,
        clipboard_copy=lambda _text: None,
        sleep=lambda _seconds: None,
    )

    with pytest.raises(WindowsOutputError, match="focus targets"):
        backend.focus_mouse_target("message_pane", click=True)
