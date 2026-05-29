from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from .output import KeyboardAction, KeyboardActionPlanner


TextOutputTarget = Literal["paste", "clipboard"]
MouseButton = Literal["left", "right"]
OutputEventKind = Literal[
    "press_keys",
    "scroll",
    "focus_mouse_target",
    "click_mouse",
    "write_text",
]


@dataclass(frozen=True)
class OutputEvent:
    kind: OutputEventKind
    keys: tuple[str, ...] = ()
    scroll_clicks: float = 0
    mouse_target: str | None = None
    mouse_button: MouseButton | None = None
    click: bool = False
    text_target: TextOutputTarget | None = None
    text_length: int = 0

    def describe(self) -> str:
        if self.kind == "press_keys":
            return f"press_keys: {'+'.join(self.keys)}"
        if self.kind == "scroll":
            return f"scroll: {self.scroll_clicks}"
        if self.kind == "write_text":
            target = self.text_target or ""
            return f"write_text: {target} length={self.text_length}"
        if self.kind == "click_mouse":
            return f"click_mouse: {self.mouse_button or ''}"
        target = self.mouse_target or ""
        return f"focus_mouse_target: {target} click={self.click}"


class OutputBackend(Protocol):
    def press_keys(self, keys: tuple[str, ...]) -> None:
        pass

    def scroll(self, clicks: float) -> None:
        pass

    def focus_mouse_target(self, target: str, *, click: bool) -> None:
        pass

    def click_mouse(self, button: MouseButton) -> None:
        pass

    def write_text(self, text: str, *, target: TextOutputTarget) -> None:
        pass


class DryRunOutputBackend:
    def __init__(self) -> None:
        self.events: list[OutputEvent] = []

    def press_keys(self, keys: tuple[str, ...]) -> None:
        self.events.append(OutputEvent(kind="press_keys", keys=keys))

    def scroll(self, clicks: float) -> None:
        self.events.append(OutputEvent(kind="scroll", scroll_clicks=clicks))

    def focus_mouse_target(self, target: str, *, click: bool) -> None:
        self.events.append(
            OutputEvent(kind="focus_mouse_target", mouse_target=target, click=click)
        )

    def click_mouse(self, button: MouseButton) -> None:
        self.events.append(OutputEvent(kind="click_mouse", mouse_button=button))

    def write_text(self, text: str, *, target: TextOutputTarget) -> None:
        self.events.append(
            OutputEvent(kind="write_text", text_target=target, text_length=len(text))
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
        if action.mouse_button is not None:
            self.backend.click_mouse(action.mouse_button)
            return action
        raise ValueError(f"Action has no output effect: {action_name}")


def dry_run_action(action_name: str) -> list[OutputEvent]:
    backend = DryRunOutputBackend()
    ActionExecutor(backend).execute(action_name)
    return backend.events
