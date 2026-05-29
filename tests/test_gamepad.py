from ai_operator_controller.gamepad import (
    AxisBinding,
    AxisActionResolver,
    HatBinding,
    HatActionResolver,
)


def test_chat_axis_emits_once_per_flick_until_released():
    resolver = AxisActionResolver(
        AxisBinding(
            axis=1,
            threshold=0.65,
            release_threshold=0.25,
            cooldown_seconds=0.45,
            negative_action="chat_previous",
            positive_action="chat_next",
        )
    )

    assert resolver.update(-0.8, now=0.0) == "chat_previous"
    assert resolver.update(-0.9, now=0.1) is None
    assert resolver.update(-0.1, now=0.2) is None
    assert resolver.update(0.8, now=0.5) == "chat_next"


def test_cursor_axis_repeats_while_held_after_cooldown():
    resolver = AxisActionResolver(
        AxisBinding(
            axis=2,
            threshold=0.55,
            release_threshold=0.2,
            cooldown_seconds=0.08,
            negative_action="cursor_left",
            positive_action="cursor_right",
            repeat=True,
        )
    )

    assert resolver.update(0.7, now=0.0) == "cursor_right"
    assert resolver.update(0.7, now=0.03) is None
    assert resolver.update(0.7, now=0.08) == "cursor_right"


def test_axis_can_scale_repeat_cooldown_by_intensity():
    resolver = AxisActionResolver(
        AxisBinding(
            axis=3,
            threshold=0.55,
            release_threshold=0.2,
            cooldown_seconds=0.08,
            negative_action="scroll_up",
            positive_action="scroll_down",
            repeat=True,
            scale_cooldown_by_intensity=True,
        )
    )

    assert resolver.update(0.6, now=0.0) == "scroll_down"
    assert resolver.update(0.6, now=0.08) is None
    assert resolver.update(0.6, now=0.14) == "scroll_down"
    assert resolver.update(1.0, now=0.20) is None
    assert resolver.update(1.0, now=0.221) == "scroll_down"


def test_dpad_hat_repeats_scroll_actions_while_held():
    resolver = HatActionResolver(
        HatBinding(
            hat=0,
            cooldown_seconds=0.08,
            up_action="scroll_up",
            down_action="scroll_down",
            repeat=True,
        )
    )

    assert resolver.update((0, 1), now=0.0) == "scroll_up"
    assert resolver.update((0, 1), now=0.03) is None
    assert resolver.update((0, 1), now=0.08) == "scroll_up"
    assert resolver.update((0, 0), now=0.09) is None
    assert resolver.update((0, -1), now=0.2) == "scroll_down"


def test_dpad_hat_emits_focus_actions_for_left_and_right():
    resolver = HatActionResolver(
        HatBinding(
            hat=0,
            cooldown_seconds=0.08,
            left_action="focus_chat_list",
            right_action="focus_message_pane",
            up_action="scroll_up",
            down_action="scroll_down",
            repeat=True,
        )
    )

    assert resolver.update((-1, 0), now=0.0) == "focus_chat_list"
    assert resolver.update((-1, 0), now=0.03) is None
    assert resolver.update((0, 0), now=0.09) is None
    assert resolver.update((1, 0), now=0.2) == "focus_message_pane"
