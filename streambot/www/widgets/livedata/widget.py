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

def debounce(wait: float):
    """
    Debounce decorator for async functions.
    Only calls the function after `wait` seconds have passed since the last call.
    Any calls during the wait period cancel the previous scheduled call.
    """
    def decorator(func):
        task_name = f"_debounce_task_{func.__name__}"

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Cancel any existing task
            task = getattr(self, task_name, None)
            if task and not task.done():
                task.cancel()

            # Schedule new task
            async def call_later():
                try:
                    await asyncio.sleep(wait)
                    await func(self, *args, **kwargs)
                except asyncio.CancelledError:
                    pass  # Ignore if cancelled by a new call

            new_task = asyncio.create_task(call_later())
            setattr(self, task_name, new_task)

        return wrapper
    return decorator


class Widget(base.Widget):
    name = "livedata"
    display_name = "Live Data"
    description = "Shows the data for a livestream session"

    active = True

    event_bus: EventBus | None = EventBus.get_instance()
    query_bus: QueryBus | None = QueryBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    twitch_viewers:int = 0
    youtube_viewers:int = 0

    twitch_raids:int = 0
    twitch_raid_viewers:int = 0

    twitch_in_ads:bool = False

    @property
    def twitch_avg_viewers(self):
        return round(self.twitch_raid_viewers / max(1, self.twitch_raids), 1)
    

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.register("OnHalfMinuteTick", self.on_tick)
        self.register("OnFiveMinuteTick", self.on_long_tick)

        self.register("TwitchRaidEvent", self.on_twitch_raid_event)

        self.register("TwitchAdStartEvent", self.on_twitch_ads_start)
        self.register("TwitchAdStopEvent", self.on_twitch_ads_stop)


    def register_queries(self, query_bus):
        self.query_bus = query_bus

    @debounce(3)
    async def update_all(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
            'twitch-raids': self.twitch_raids,
            'twitch-raid-viewers': self.twitch_avg_viewers,
        }))

    @debounce(3)
    async def update_viewers(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
        }))

    async def update_in_ads(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-in-ads': self.twitch_in_ads,
        }))
        
    async def update_raids(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-raids': self.twitch_raids,
            'twitch-raid-viewers': self.twitch_avg_viewers,
        }))

    async def get_viewers(self):
        resp:Response = await self.query_bus.query("GetTwitchViewers", {})
        self.twitch_viewers = resp.get()
        resp:Response = await self.query_bus.query("GetYouTubeViewers", {})
        self.youtube_viewers = resp.get()

    async def on_tick(self, _:EventData):
        await self.get_viewers()
        await self.update_viewers()

    async def on_long_tick(self, _:EventData):
        await self.get_viewers()
        await self.update_all()

    def context(self):
        return {
            'twitch_viewers': self.twitch_viewers,
            'youtube_viewers': self.youtube_viewers,

            'twitch_raids': self.twitch_raids,
            'twitch_raid_viewers': self.twitch_avg_viewers,

            'twitch_in_ads': self.twitch_in_ads,
        }
    
    # -=-=- Events -=-=- #

    async def on_twitch_raid_event(self, data:TwitchEventData[ChannelRaidEvent]):
        print(f"[livedata widget] Raid {data.data.event.from_broadcaster_user_name} with {data.data.event.viewers}")
        self.twitch_raids += 1
        self.twitch_raid_viewers += data.data.event.viewers
        await self.update_raids()

    async def on_twitch_ads_start(self, data:TwitchEventData[ChannelAdBreakBeginEvent]):
        self.twitch_in_ads = True
        self.update_in_ads()

    async def on_twitch_ads_stop(self, data:TwitchEventData[ChannelAdBreakBeginEvent]):
        self.twitch_in_ads = False
        self.update_in_ads()

