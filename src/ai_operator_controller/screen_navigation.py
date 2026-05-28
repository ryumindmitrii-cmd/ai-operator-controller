from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .actions import validate_action_name

Bounds = tuple[int, int, int, int]


@dataclass(frozen=True)
class ClickPoint:
    x: int
    y: int


@dataclass(frozen=True)
class ChatItem:
    index: int
    bounds: Bounds
    is_active: bool
    confidence: float

    @property
    def center(self) -> ClickPoint:
        left, top, right, bottom = self.bounds
        return ClickPoint(x=(left + right) // 2, y=(top + bottom) // 2)


@dataclass(frozen=True)
class ChatNavigationResult:
    clicked: bool
    fallback_action: str | None
    reason: str


class MouseController(Protocol):
    def click(self, point: ClickPoint) -> None:
        ...


class ChatNavigator:
    def __init__(self, mouse: MouseController, *, min_confidence: float = 0.8) -> None:
        self.mouse = mouse
        self.min_confidence = min_confidence
        self._screen_nav_index: int | None = None

    def navigate(self, items: list[ChatItem], action_name: str) -> ChatNavigationResult:
        validate_action_name(action_name)
        if action_name not in {"chat_next", "chat_previous"}:
            raise ValueError(f"Unsupported screen navigation action: {action_name}")

        if not items:
            return self._fallback(action_name, "no_chat_items")

        ordered_items = sorted(items, key=lambda item: item.index)
        active_position = self._active_position(ordered_items)
        if active_position is None:
            return ChatNavigationResult(
                clicked=False,
                fallback_action=None,
                reason="no_active_chat",
            )
        target_position = active_position + (1 if action_name == "chat_next" else -1)
        if target_position < 0 or target_position >= len(ordered_items):
            return self._fallback(action_name, "edge_of_list")

        target_item = ordered_items[target_position]
        confidence = target_item.confidence
        if 0 <= active_position < len(ordered_items):
            active_item = ordered_items[active_position]
            confidence = min(active_item.confidence, target_item.confidence)
        if confidence < self.min_confidence:
            return self._fallback(action_name, "low_confidence")

        self.mouse.click(target_item.center)
        self._screen_nav_index = target_position
        return ChatNavigationResult(clicked=True, fallback_action=None, reason="clicked")

    def _active_position(self, items: list[ChatItem]) -> int | None:
        for position, item in enumerate(items):
            if item.is_active:
                self._screen_nav_index = position
                return position
        if self._screen_nav_index is not None and self._screen_nav_index < len(items):
            return self._screen_nav_index
        return None

    def _fallback(self, action_name: str, reason: str) -> ChatNavigationResult:
        return ChatNavigationResult(clicked=False, fallback_action=action_name, reason=reason)


class PywinautoCodexChatReader:
    def __init__(self, *, title_re: str = ".*Codex.*") -> None:
        self.title_re = title_re

    def read_chat_items(self) -> list[ChatItem]:
        try:
            from pywinauto import Desktop
        except ImportError:
            return []

        try:
            window = Desktop(backend="uia").window(title_re=self.title_re)
            window_rectangle = window.rectangle()
            controls = []
            for control_type in ("ListItem", "TreeItem", "DataItem"):
                controls.extend(window.descendants(control_type=control_type))
        except Exception:
            return []

        items: list[ChatItem] = []
        for control in controls:
            item = self._chat_item_from_control(len(items), control, window_rectangle)
            if item is not None:
                items.append(item)
        return items

    def _chat_item_from_control(
        self,
        index: int,
        control: object,
        window_rectangle: object,
    ) -> ChatItem | None:
        try:
            rectangle = control.rectangle()
            width = int(rectangle.right - rectangle.left)
            height = int(rectangle.bottom - rectangle.top)
            window_left = int(window_rectangle.left)
            window_top = int(window_rectangle.top)
            window_bottom = int(window_rectangle.bottom)
            window_width = int(window_rectangle.right - window_rectangle.left)
        except Exception:
            return None

        if width < 80 or height < 16 or height > 110:
            return None
        if int(rectangle.top) < window_top + 70 or int(rectangle.bottom) > window_bottom - 70:
            return None
        center_x = int((rectangle.left + rectangle.right) / 2)
        if center_x > window_left + int(window_width * 0.45):
            return None

        is_active = _safe_bool(control, "is_keyboard_focus") or _safe_bool(control, "is_selected")
        confidence = 0.9 if is_active else 0.82
        return ChatItem(
            index=index,
            bounds=(
                int(rectangle.left),
                int(rectangle.top),
                int(rectangle.right),
                int(rectangle.bottom),
            ),
            is_active=is_active,
            confidence=confidence,
        )


def _safe_bool(obj: object, method_name: str) -> bool:
    method = getattr(obj, method_name, None)
    if method is None:
        return False
    try:
        return bool(method())
    except Exception:
        return False
