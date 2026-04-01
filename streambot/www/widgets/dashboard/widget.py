#! /usr/bin/env python3

"""Dashboard widget for the WebUI."""

from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, ChatMessageOutData, Platform
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals.event_bus import EventBus


class Widget(base.Widget):
    name = "dashboard"
    display_name = "Dashboard"
    description = "Dashboard for dashboarding...."

    # event_bus: EventBus | None = EventBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

