from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import time
from typing import Any, Callable, Protocol

from .gamepad import GamepadActionResult, GamepadActionRuntime, GamepadBindings, HatValue


@dataclass(frozen=True)
class GamepadState:
    buttons: Mapping[int, bool]
    axes: Mapping[int, float]
    hats: Mapping[int, HatValue]


@dataclass(frozen=True)
class PolledGamepadAction:
    input_kind: str
    input_name: str
    raw_index: int
    raw_value: str
    result: GamepadActionResult

    def describe_input(self) -> str:
        return f"Input: {self.input_kind} {self.input_name} {self.raw_value}"


class GamepadStateReader(Protocol):
    controller_name: str

    def read_state(self) -> GamepadState:
        pass

    def close(self) -> None:
        pass


def poll_gamepad_state(
    runtime: GamepadActionRuntime,
    bindings: GamepadBindings,
    state: GamepadState,
    *,
    now: float,
) -> list[PolledGamepadAction]:
    actions: list[PolledGamepadAction] = []

    for name, binding in sorted(bindings.buttons.items()):
        pressed = bool(state.buttons.get(binding.button, False))
        result = runtime.update_button(name, pressed, now=now)
        if result is not None:
            actions.append(
                PolledGamepadAction(
                    input_kind="button",
                    input_name=name,
                    raw_index=binding.button,
                    raw_value="down" if pressed else "up",
                    result=result,
                )
            )

    for name, binding in sorted(bindings.axes.items()):
        value = float(state.axes.get(binding.axis, 0.0))
        result = runtime.update_axis(name, value, now=now)
        if result is not None:
            actions.append(
                PolledGamepadAction(
                    input_kind="axis",
                    input_name=name,
                    raw_index=binding.axis,
                    raw_value=f"{value:.3f}",
                    result=result,
                )
            )

    for name, binding in sorted(bindings.hats.items()):
        value = state.hats.get(binding.hat, (0, 0))
        result = runtime.update_hat(name, value, now=now)
        if result is not None:
            actions.append(
                PolledGamepadAction(
                    input_kind="hat",
                    input_name=name,
                    raw_index=binding.hat,
                    raw_value=f"{value[0]} {value[1]}",
                    result=result,
                )
            )

    return actions


class PygameGamepadReader:
    def __init__(self, *, device_index: int = 0) -> None:
        try:
            import pygame
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "pygame is required for listen-gamepad; install the package with "
                'python -m pip install -e ".[dev]"'
            ) from exc

        self._pygame = pygame
        pygame.init()
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count <= 0:
            raise RuntimeError("No joystick devices detected")
        if device_index < 0 or device_index >= joystick_count:
            raise RuntimeError(
                f"Joystick index {device_index} is unavailable; detected {joystick_count}"
            )

        self._joystick = pygame.joystick.Joystick(device_index)
        self.controller_name = str(self._joystick.get_name())

    def read_state(self) -> GamepadState:
        self._pygame.event.pump()
        return GamepadState(
            buttons={
                index: bool(self._joystick.get_button(index))
                for index in range(self._joystick.get_numbuttons())
            },
            axes={
                index: float(self._joystick.get_axis(index))
                for index in range(self._joystick.get_numaxes())
            },
            hats={
                index: _hat_value(self._joystick.get_hat(index))
                for index in range(self._joystick.get_numhats())
            },
        )

    def close(self) -> None:
        self._pygame.joystick.quit()
        self._pygame.quit()


def listen_gamepad_dry_run(
    bindings: GamepadBindings,
    reader: GamepadStateReader,
    *,
    max_events: int | None = None,
    poll_interval_seconds: float = 0.03,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
    emit: Callable[[PolledGamepadAction], None] | None = None,
) -> int:
    if max_events is not None and max_events < 0:
        raise ValueError("max_events must be non-negative")
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")

    runtime = GamepadActionRuntime(bindings)
    emitted_count = 0

    try:
        while max_events is None or emitted_count < max_events:
            state = reader.read_state()
            actions = poll_gamepad_state(runtime, bindings, state, now=clock())
            for action in actions:
                if emit is not None:
                    emit(action)
                emitted_count += 1
                if max_events is not None and emitted_count >= max_events:
                    return emitted_count
            sleep(poll_interval_seconds)
    except KeyboardInterrupt:
        return emitted_count
    finally:
        reader.close()

    return emitted_count


def _hat_value(value: Any) -> HatValue:
    x, y = value
    return int(x), int(y)
