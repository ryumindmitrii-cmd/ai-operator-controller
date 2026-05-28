from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .actions import validate_action_name

AxisDirection = Literal["negative", "positive"]


@dataclass(frozen=True)
class AxisBinding:
    axis: int
    threshold: float
    release_threshold: float
    cooldown_seconds: float
    negative_action: str | None = None
    positive_action: str | None = None
    repeat: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.release_threshold < self.threshold <= 1:
            raise ValueError("axis thresholds must satisfy 0 < release_threshold < threshold <= 1")

        for action in (self.negative_action, self.positive_action):
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
