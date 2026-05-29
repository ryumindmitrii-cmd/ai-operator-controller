from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from .output import KeyboardAction, KeyboardActionPlanner


OutputEventKind = Literal["press_keys", "scroll", "focus_mouse_target"]


@dataclass(frozen=True)
class OutputEvent:
    kind: OutputEventKind
    keys: tuple[str, ...] = ()
    scroll_clicks: int = 0
    mouse_target: str | None = None
    click: bool = False

    def describe(self) -> str:
        if self.kind == "press_keys":
            return f"press_keys: {'+'.join(self.keys)}"
        if self.kind == "scroll":
            return f"scroll: {self.scroll_clicks}"
        target = self.mouse_target or ""
        return f"focus_mouse_target: {target} click={self.click}"


class OutputBackend(Protocol):
    def press_keys(self, keys: tuple[str, ...]) -> None:
        pass

    def scroll(self, clicks: int) -> None:
        pass

    def focus_mouse_target(self, target: str, *, click: bool) -> None:
        pass


class DryRunOutputBackend:
    def __init__(self) -> None:
        self.events: list[OutputEvent] = []

    def press_keys(self, keys: tuple[str, ...]) -> None:
        self.events.append(OutputEvent(kind="press_keys", keys=keys))

    def scroll(self, clicks: int) -> None:
        self.events.append(OutputEvent(kind="scroll", scroll_clicks=clicks))

    def focus_mouse_target(self, target: str, *, click: bool) -> None:
        self.events.append(
            OutputEvent(kind="focus_mouse_target", mouse_target=target, click=click)
        )


class ActionExecutor:
    def __init__(
        self,
        backend: OutputBackend,
        planner: KeyboardActionPlanner | None = None,
    ) -> None:
        self.backend = backend
        self.planner = planner or KeyboardActionPlanner()

    def execute(self, action_name: str) -> KeyboardAction:
        action = self.planner.plan(action_name)
        if action.keys:
            self.backend.press_keys(action.keys)
            return action
        if action.scroll_clicks:
            self.backend.scroll(action.scroll_clicks)
            return action
        if action.mouse_target is not None:
            self.backend.focus_mouse_target(action.mouse_target, click=action.click)
            return action
        raise ValueError(f"Action has no output effect: {action_name}")


def dry_run_action(action_name: str) -> list[OutputEvent]:
    backend = DryRunOutputBackend()
    ActionExecutor(backend).execute(action_name)
    return backend.events
