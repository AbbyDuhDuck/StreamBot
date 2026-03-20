#! /usr/bin/env python3

"""Chat widget for the WebUI."""

import random

from streambot.service.builtin.chat_youtube import UpdateViewersYoutubeData
from streambot.service.builtin.chat_twitch import TwitchEventData
from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, ChatMessageOutData, Platform
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals import EventBus, EventData, QueryBus, Response

from twitchAPI.object.eventsub import ChannelRaidEvent, ChannelAdBreakBeginEvent

import asyncio
from functools import wraps


class Widget(base.Widget):
    name = "counter"
    display_name = "Counter"
    description = "counts..."

    # active = True

    event_bus: EventBus | None = EventBus.get_instance()
    query_bus: QueryBus | None = QueryBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    count = 0
    

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.register("WSMessageCounter", self.event_ws_message)

    def register_queries(self, query_bus):
        self.query_bus = query_bus


    async def event_ws_message(self, event:WSMessageData):
        print(f"Received WSMessage ({event.event}): {event.data}")
        if event.event == "decrement":
            self.count -= 1
            await self.update_count()
        if event.event == "increment":
            self.count += 1
            await self.update_count()

    async def update_count(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="counter", event='update', message={
            'counter-count': self.count,
        }))

    def context(self):
        return {
            'counter_count': self.count,
        }
    
    # -=-=- Events -=-=- #


