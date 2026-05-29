from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from .actions import validate_action_name
from .executor import ActionExecutor, DryRunOutputBackend, OutputEvent

AxisDirection = Literal["negative", "positive"]
HatDirection = Literal["left", "right", "up", "down"]
HatValue = tuple[int, int]


@dataclass(frozen=True)
class AxisBinding:
    axis: int
    threshold: float
    release_threshold: float
    cooldown_seconds: float
    action: str | None = None
    negative_action: str | None = None
    positive_action: str | None = None
    repeat: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.release_threshold < self.threshold <= 1:
            raise ValueError("axis thresholds must satisfy 0 < release_threshold < threshold <= 1")

        for action in (self.action, self.negative_action, self.positive_action):
            if action is not None:
                validate_action_name(action)


class AxisActionResolver:
    def __init__(self, binding: AxisBinding) -> None:
        self.binding = binding
        self._active_direction: AxisDirection | None = None
        self._last_action_at: float | None = None

    def update(self, value: float, *, now: float) -> str | None:
        direction = self._direction_for_value(value)
        if direction is None:
            self._active_direction = None
            return None

        action = self._action_for_direction(direction)
        if action is None:
            self._active_direction = direction
            return None

        if not self._can_emit(direction, now):
            return None

        self._active_direction = direction
        self._last_action_at = now
        return action

    def _direction_for_value(self, value: float) -> AxisDirection | None:
        if abs(value) <= self.binding.release_threshold:
            return None
        if value <= -self.binding.threshold:
            return "negative"
        if value >= self.binding.threshold:
            return "positive"
        return self._active_direction

    def _action_for_direction(self, direction: AxisDirection) -> str | None:
        if self.binding.action is not None:
            if direction == "positive":
                return self.binding.action
            return None
        if direction == "negative":
            return self.binding.negative_action
        return self.binding.positive_action

    def _can_emit(self, direction: AxisDirection, now: float) -> bool:
        if self._active_direction != direction:
            return self._cooldown_elapsed(now)
        return self.binding.repeat and self._cooldown_elapsed(now)

    def _cooldown_elapsed(self, now: float) -> bool:
        if self._last_action_at is None:
            return True
        return now - self._last_action_at >= self.binding.cooldown_seconds


@dataclass(frozen=True)
class ButtonBinding:
    button: int
    action: str
    cooldown_seconds: float = 0.0
    repeat: bool = False

    def __post_init__(self) -> None:
        if self.button < 0:
            raise ValueError("button index must be non-negative")
        if self.cooldown_seconds < 0:
            raise ValueError("button cooldown must be non-negative")
        validate_action_name(self.action)


class ButtonActionResolver:
    def __init__(self, binding: ButtonBinding) -> None:
        self.binding = binding
        self._pressed = False
        self._last_action_at: float | None = None

    def update(self, pressed: bool, *, now: float) -> str | None:
        if not pressed:
            self._pressed = False
            return None

        if not self._pressed:
            self._pressed = True
            self._last_action_at = now
            return self.binding.action

        if not self.binding.repeat:
            return None
        if not self._cooldown_elapsed(now):
            return None

        self._last_action_at = now
        return self.binding.action

    def _cooldown_elapsed(self, now: float) -> bool:
        if self._last_action_at is None:
            return True
        return now - self._last_action_at >= self.binding.cooldown_seconds


@dataclass(frozen=True)
class HatBinding:
    hat: int
    cooldown_seconds: float
    left_action: str | None = None
    right_action: str | None = None
    up_action: str | None = None
    down_action: str | None = None
    repeat: bool = False

    def __post_init__(self) -> None:
        if self.hat < 0:
            raise ValueError("hat index must be non-negative")
        if self.cooldown_seconds < 0:
            raise ValueError("hat cooldown must be non-negative")

        for action in (
            self.left_action,
            self.right_action,
            self.up_action,
            self.down_action,
        ):
            if action is not None:
                validate_action_name(action)


class HatActionResolver:
    def __init__(self, binding: HatBinding) -> None:
        self.binding = binding
        self._active_direction: HatDirection | None = None
        self._last_action_at: float | None = None

    def update(self, value: HatValue, *, now: float) -> str | None:
        direction = self._direction_for_value(value)
        if direction is None:
            self._active_direction = None
            return None

        action = self._action_for_direction(direction)
        if action is None:
            self._active_direction = direction
            return None

        if not self._can_emit(direction, now):
            return None

        self._active_direction = direction
        self._last_action_at = now
        return action

    def _direction_for_value(self, value: HatValue) -> HatDirection | None:
        x, y = value
        if y > 0:
            return "up"
        if y < 0:
            return "down"
        if x < 0:
            return "left"
        if x > 0:
            return "right"
        return None

    def _action_for_direction(self, direction: HatDirection) -> str | None:
        if direction == "left":
            return self.binding.left_action
        if direction == "right":
            return self.binding.right_action
        if direction == "up":
            return self.binding.up_action
        return self.binding.down_action

    def _can_emit(self, direction: HatDirection, now: float) -> bool:
        if self._active_direction != direction:
            return self._cooldown_elapsed(now)
        return self.binding.repeat and self._cooldown_elapsed(now)

    def _cooldown_elapsed(self, now: float) -> bool:
        if self._last_action_at is None:
            return True
        return now - self._last_action_at >= self.binding.cooldown_seconds


@dataclass(frozen=True)
class GamepadBindings:
    buttons: dict[str, ButtonBinding]
    axes: dict[str, AxisBinding]
    hats: dict[str, HatBinding]


@dataclass(frozen=True)
class GamepadActionResult:
    action_name: str
    output_events: tuple[OutputEvent, ...] = ()
    unsupported_reason: str | None = None


class GamepadActionRuntime:
    def __init__(self, bindings: GamepadBindings) -> None:
        self.backend = DryRunOutputBackend()
        self.executor = ActionExecutor(self.backend)
        self.button_resolvers = {
            name: ButtonActionResolver(binding) for name, binding in bindings.buttons.items()
        }
        self.axis_resolvers = {
            name: AxisActionResolver(binding) for name, binding in bindings.axes.items()
        }
        self.hat_resolvers = {
            name: HatActionResolver(binding) for name, binding in bindings.hats.items()
        }

    def update_button(self, name: str, pressed: bool, *, now: float) -> GamepadActionResult | None:
        action_name = self.button_resolvers[name].update(pressed, now=now)
        if action_name is None:
            return None
        return self._execute(action_name)

    def update_axis(self, name: str, value: float, *, now: float) -> GamepadActionResult | None:
        action_name = self.axis_resolvers[name].update(value, now=now)
        if action_name is None:
            return None
        return self._execute(action_name)

    def update_hat(self, name: str, value: HatValue, *, now: float) -> GamepadActionResult | None:
        action_name = self.hat_resolvers[name].update(value, now=now)
        if action_name is None:
            return None
        return self._execute(action_name)

    def _execute(self, action_name: str) -> GamepadActionResult:
        event_start = len(self.backend.events)
        try:
            self.executor.execute(action_name)
        except ValueError as exc:
            return GamepadActionResult(action_name=action_name, unsupported_reason=str(exc))
        return GamepadActionResult(
            action_name=action_name,
            output_events=tuple(self.backend.events[event_start:]),
        )


def bindings_from_profile(profile: Mapping[str, Any]) -> GamepadBindings:
    gamepad = _as_mapping(profile["gamepad"])
    return GamepadBindings(
        buttons={
            name: _button_binding_from_profile(_as_mapping(binding))
            for name, binding in _as_mapping(gamepad["buttons"]).items()
        },
        axes={
            name: _axis_binding_from_profile(_as_mapping(binding))
            for name, binding in _as_mapping(gamepad["axes"]).items()
        },
        hats={
            name: _hat_binding_from_profile(_as_mapping(binding))
            for name, binding in _as_mapping(gamepad["hats"]).items()
        },
    )


def _button_binding_from_profile(binding: Mapping[str, Any]) -> ButtonBinding:
    return ButtonBinding(
        button=int(binding["button"]),
        action=str(binding["action"]),
        cooldown_seconds=float(binding.get("cooldown_seconds", 0.0)),
        repeat=bool(binding.get("repeat", False)),
    )


def _axis_binding_from_profile(binding: Mapping[str, Any]) -> AxisBinding:
    return AxisBinding(
        axis=int(binding["axis"]),
        threshold=float(binding["threshold"]),
        release_threshold=float(binding["release_threshold"]),
        cooldown_seconds=float(binding["cooldown_seconds"]),
        action=_optional_str(binding.get("action")),
        negative_action=_optional_str(binding.get("negative_action")),
        positive_action=_optional_str(binding.get("positive_action")),
        repeat=bool(binding.get("repeat", False)),
    )


def _hat_binding_from_profile(binding: Mapping[str, Any]) -> HatBinding:
    return HatBinding(
        hat=int(binding["hat"]),
        cooldown_seconds=float(binding["cooldown_seconds"]),
        left_action=_optional_str(binding.get("left_action")),
        right_action=_optional_str(binding.get("right_action")),
        up_action=_optional_str(binding.get("up_action")),
        down_action=_optional_str(binding.get("down_action")),
        repeat=bool(binding.get("repeat", False)),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("profile value must be a mapping")
    return value
