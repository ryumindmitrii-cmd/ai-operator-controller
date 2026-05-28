from ai_operator_controller.output import KeyboardActionPlanner


def test_cursor_actions_map_to_arrow_keys():
    planner = KeyboardActionPlanner()

    assert planner.plan("cursor_left").keys == ("left",)
    assert planner.plan("cursor_right").keys == ("right",)
    assert planner.plan("cursor_up").keys == ("up",)
    assert planner.plan("cursor_down").keys == ("down",)


def test_space_action_maps_to_space_key():
    planner = KeyboardActionPlanner()

    assert planner.plan("space").keys == ("space",)


def test_chat_actions_have_keyboard_fallbacks():
    planner = KeyboardActionPlanner()

    assert planner.plan("chat_previous").keys == ("ctrl", "shift", "tab")
    assert planner.plan("chat_next").keys == ("ctrl", "tab")


def test_scroll_actions_map_to_mouse_wheel_clicks():
    planner = KeyboardActionPlanner()

    assert planner.plan("scroll_up").keys == ()
    assert planner.plan("scroll_up").scroll_clicks > 0
    assert planner.plan("scroll_down").keys == ()
    assert planner.plan("scroll_down").scroll_clicks < 0


def test_focus_actions_map_to_mouse_targets():
    planner = KeyboardActionPlanner()

    chat_list = planner.plan("focus_chat_list")
    message_pane = planner.plan("focus_message_pane")

    assert chat_list.keys == ()
    assert chat_list.mouse_target == "chat_list"
    assert chat_list.click is False
    assert message_pane.keys == ()
    assert message_pane.mouse_target == "message_pane"
    assert message_pane.click is True
