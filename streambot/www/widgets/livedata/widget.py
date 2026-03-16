#! /usr/bin/env python3

"""Chat widget for the WebUI."""

import random

from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, MessageOutData, Platform
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals.event_bus import EventBus


class Widget(base.Widget):
    name = "livedata"
    display_name = "Live Data"
    description = "Shows the data for a livestream session"

    active = True

    event_bus: EventBus | None = EventBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    twitch_viewers:int = 13
    youtube_viewers:int = 10

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.register("ChatMessage", self.event_chat_message)

    async def event_chat_message(self, event:ChatMessageData):
        # print(f"ChatMessage: {event.user}: {event.message}")
        self.twitch_viewers = max(0, self.twitch_viewers + random.randint(-2, 2))
        self.youtube_viewers = max(0, self.youtube_viewers + random.randint(-2, 2))
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
        }))