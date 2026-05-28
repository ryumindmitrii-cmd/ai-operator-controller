from dataclasses import dataclass

from ai_operator_controller.screen_navigation import (
    ChatItem,
    ChatNavigationResult,
    ChatNavigator,
    ClickPoint,
)


@dataclass
class FakeMouse:
    clicked: ClickPoint | None = None

    def click(self, point: ClickPoint) -> None:
        self.clicked = point


def test_chat_navigator_clicks_next_chat_when_confident():
    mouse = FakeMouse()
    navigator = ChatNavigator(mouse=mouse, min_confidence=0.8)
    items = [
        ChatItem(index=0, bounds=(10, 10, 110, 40), is_active=True, confidence=0.95),
        ChatItem(index=1, bounds=(10, 50, 110, 80), is_active=False, confidence=0.95),
    ]

    result = navigator.navigate(items, "chat_next")

    assert result == ChatNavigationResult(clicked=True, fallback_action=None, reason="clicked")
    assert mouse.clicked == ClickPoint(x=60, y=65)


def test_chat_navigator_starts_from_edge_when_active_chat_is_unknown():
    mouse = FakeMouse()
    navigator = ChatNavigator(mouse=mouse, min_confidence=0.8)
    items = [
        ChatItem(index=0, bounds=(10, 10, 110, 40), is_active=False, confidence=0.95),
        ChatItem(index=1, bounds=(10, 50, 110, 80), is_active=False, confidence=0.95),
    ]

    first_result = navigator.navigate(items, "chat_next")
    second_result = navigator.navigate(items, "chat_next")

    assert first_result == ChatNavigationResult(clicked=True, fallback_action=None, reason="clicked")
    assert second_result == ChatNavigationResult(clicked=True, fallback_action=None, reason="clicked")
    assert mouse.clicked == ClickPoint(x=60, y=65)


def test_chat_navigator_can_start_from_bottom_when_active_chat_is_unknown():
    mouse = FakeMouse()
    navigator = ChatNavigator(mouse=mouse, min_confidence=0.8)
    items = [
        ChatItem(index=0, bounds=(10, 10, 110, 40), is_active=False, confidence=0.95),
        ChatItem(index=1, bounds=(10, 50, 110, 80), is_active=False, confidence=0.95),
    ]

    result = navigator.navigate(items, "chat_previous")

    assert result == ChatNavigationResult(clicked=True, fallback_action=None, reason="clicked")
    assert mouse.clicked == ClickPoint(x=60, y=65)


def test_chat_navigator_falls_back_when_confidence_is_low():
    mouse = FakeMouse()
    navigator = ChatNavigator(mouse=mouse, min_confidence=0.8)
    items = [
        ChatItem(index=0, bounds=(10, 10, 110, 40), is_active=True, confidence=0.5),
        ChatItem(index=1, bounds=(10, 50, 110, 80), is_active=False, confidence=0.5),
    ]

    result = navigator.navigate(items, "chat_next")

    assert result == ChatNavigationResult(
        clicked=False,
        fallback_action="chat_next",
        reason="low_confidence",
    )
    assert mouse.clicked is None
