from __future__ import annotations

import sys
import time
from typing import Callable, Literal, Protocol

from .executor import MouseButton, TextOutputTarget


class WindowsOutputError(RuntimeError):
    pass


class KeyboardController(Protocol):
    def press(self, key) -> None:
        pass

    def release(self, key) -> None:
        pass


class MouseController(Protocol):
    def scroll(self, dx: float, dy: float) -> None:
        pass

    def click(self, button) -> None:
        pass


class WindowsDesktopOutputBackend:
    def __init__(
        self,
        *,
        keyboard_controller: KeyboardController | None = None,
        mouse_controller: MouseController | None = None,
        key_namespace=None,
        button_namespace=None,
        clipboard_copy: Callable[[str], None] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        paste_delay_seconds: float = 0.05,
    ) -> None:
        if paste_delay_seconds < 0:
            raise ValueError("paste_delay_seconds must be non-negative")

        if keyboard_controller is None or mouse_controller is None:
            if sys.platform != "win32":
                raise WindowsOutputError("Windows output backend requires Windows")
            keyboard_controller, mouse_controller, key_namespace, button_namespace = (
                self._load_pynput_controllers()
            )
        if key_namespace is None or button_namespace is None:
            raise WindowsOutputError("keyboard and mouse namespaces are required")
        if clipboard_copy is None:
            clipboard_copy = self._load_clipboard_copy()

        self._keyboard = keyboard_controller
        self._mouse = mouse_controller
        self._key = key_namespace
        self._button = button_namespace
        self._clipboard_copy = clipboard_copy
        self._sleep = sleep
        self._paste_delay_seconds = paste_delay_seconds

    def press_keys(self, keys: tuple[str, ...]) -> None:
        resolved_keys = tuple(self._resolve_key(key) for key in keys)
        pressed_keys = []
        try:
            for key in resolved_keys:
                self._keyboard.press(key)
                pressed_keys.append(key)
        finally:
            for key in reversed(pressed_keys):
                self._keyboard.release(key)

    def scroll(self, clicks: float) -> None:
        self._mouse.scroll(0, clicks)

    def focus_mouse_target(self, target: str, *, click: bool) -> None:
        raise WindowsOutputError(
            f"focus targets are not implemented for real output yet: {target}"
        )

    def click_mouse(self, button: MouseButton) -> None:
        self._mouse.click(self._resolve_button(button))

    def write_text(self, text: str, *, target: TextOutputTarget) -> None:
        self._clipboard_copy(text)
        if target == "clipboard":
            return
        if target == "paste":
            self.press_keys(("ctrl", "v"))
            self._sleep(self._paste_delay_seconds)
            return
        raise WindowsOutputError(f"unsupported text output target: {target}")

    def _resolve_key(self, key: str):
        if len(key) == 1:
            return key
        key_map = {
            "alt": self._key.alt,
            "backspace": self._key.backspace,
            "ctrl": self._key.ctrl,
            "down": self._key.down,
            "enter": self._key.enter,
            "left": self._key.left,
            "right": self._key.right,
            "shift": self._key.shift,
            "space": self._key.space,
            "tab": self._key.tab,
            "up": self._key.up,
        }
        try:
            return key_map[key]
        except KeyError as exc:
            raise WindowsOutputError(f"unsupported key for Windows output: {key}") from exc

    def _resolve_button(self, button: MouseButton):
        button_map: dict[Literal["left", "right"], object] = {
            "left": self._button.left,
            "right": self._button.right,
        }
        try:
            return button_map[button]
        except KeyError as exc:
            raise WindowsOutputError(f"unsupported mouse button: {button}") from exc

    @staticmethod
    def _load_pynput_controllers():
        try:
            from pynput import keyboard, mouse
        except Exception as exc:  # pragma: no cover - depends on local desktop stack
            raise WindowsOutputError(f"failed to load pynput controllers: {exc}") from exc
        return keyboard.Controller(), mouse.Controller(), keyboard.Key, mouse.Button

    @staticmethod
    def _load_clipboard_copy() -> Callable[[str], None]:
        try:
            import pyperclip
        except Exception as exc:  # pragma: no cover - depends on local desktop stack
            raise WindowsOutputError(f"failed to load clipboard backend: {exc}") from exc
        return pyperclip.copy


def create_windows_output_backend() -> WindowsDesktopOutputBackend:
    return WindowsDesktopOutputBackend()
