#! /usr/bin/env python3

"""Chat widget for the WebUI."""

import random

from streambot.service.builtin.chat_youtube import UpdateViewersYoutubeData
from streambot.service.builtin.chat_twitch import TwitchEventData
from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, ChatMessageOutData, Platform, LiveState, ChatStatusChangeData
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals import EventBus, EventData, QueryBus, Response
from streambot.core.decorators import debounce

from twitchAPI.object.eventsub import ChannelRaidEvent, ChannelAdBreakBeginEvent

import asyncio
from functools import wraps


class Widget(base.Widget):
    name = "livedata"
    display_name = "Live Data"
    description = "Shows the data for a livestream session"

    active = True

    event_bus: EventBus | None = EventBus.get_instance()
    query_bus: QueryBus | None = QueryBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    twitch_viewers:int = 0
    twitch_live_state:LiveState = LiveState.CONNECTING
    youtube_viewers:int = 0
    youtube_live_state:LiveState = LiveState.CONNECTING

    twitch_raids:int = 0
    twitch_raid_viewers:int = 0

    twitch_in_ads:bool = False
    twitch_ad_dur:int = 0

    @property
    def twitch_avg_viewers(self):
        return round(self.twitch_raid_viewers / max(1, self.twitch_raids), 1)
    

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus

        self.register("TwitchRaidEvent", self.on_twitch_raid_event)

        self.register("TwitchAdStartEvent", self.on_twitch_ad_start)
        self.register("TwitchAdStopEvent", self.on_twitch_ad_stop)

        self.register("ChatStatusChangeEvent", self.on_status_change)


    def register_queries(self, query_bus):
        self.query_bus = query_bus

    # -=-=- #

    @debounce(3)
    async def update_all(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
            'twitch-raids': self.twitch_raids,
            'twitch-raid-viewers': self.twitch_avg_viewers,
            'twitch-live-state': self.twitch_live_state.name.lower(),
            'youtube-live-state': self.youtube_live_state.name.lower(),
        }))

    @debounce(3)
    async def update_status_change(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
            'twitch-live-state': self.twitch_live_state.name.lower(),
            'youtube-live-state': self.youtube_live_state.name.lower(),
        }))

    # -=-=- #

    @debounce(3)
    async def update_viewers(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-viewers': self.twitch_viewers,
            'youtube-viewers': self.youtube_viewers,
        }))

    @debounce(3)
    async def update_live_state(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-live-state': self.twitch_live_state.name.lower(),
            'youtube-live-state': self.youtube_live_state.name.lower(),
        }))

    async def update_in_ads(self):
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="livedata", event='update', message={
            'twitch-in-ads': self.twitch_in_ads,
            'twitch-ad-dur': self.twitch_ad_dur,
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

    async def get_live_state(self):
        resp:Response = await self.query_bus.query("GetTwitchLiveState", {})
        self.twitch_live_state = resp.get()
        resp:Response = await self.query_bus.query("GetYouTubeLiveState", {})
        self.youtube_live_state = resp.get()
    
    # -=-=- #

    def context(self):
        return {
            'twitch_viewers': self.twitch_viewers,
            'youtube_viewers': self.youtube_viewers,

            'twitch_raids': self.twitch_raids,
            'twitch_raid_viewers': self.twitch_avg_viewers,

            'twitch_in_ads': self.twitch_in_ads,

            'twitch_live_state': self.twitch_live_state.name.lower(),
            'youtube_live_state': self.youtube_live_state.name.lower(),
        }
    
    # -=-=- Events -=-=- #

    async def on_twitch_raid_event(self, data:TwitchEventData[ChannelRaidEvent]):
        print(f"[livedata widget] Raid {data.data.event.from_broadcaster_user_name} with {data.data.event.viewers}")
        self.twitch_raids += 1
        self.twitch_raid_viewers += data.data.event.viewers
        await self.update_raids()

    async def on_twitch_ad_start(self, data:TwitchEventData[ChannelAdBreakBeginEvent]):
        self.twitch_in_ads = True
        self.twitch_ad_dur = data.data.event.duration_seconds
        await self.update_in_ads()

    async def on_twitch_ad_stop(self, data:TwitchEventData[ChannelAdBreakBeginEvent]):
        self.twitch_in_ads = False
        await self.update_in_ads()

    async def on_status_change(self, data:ChatStatusChangeData):
        print(f"{data.platform.value} Status Changed")
        if data.platform is Platform.TWITCH:
            await self.on_twitch_status_change(data, False)
        if data.platform is Platform.YOUTUBE:
            await self.on_youtube_status_change(data, False)
        await self.update_status_change()

    async def on_twitch_status_change(self, data:ChatStatusChangeData, push:bool=True):
        if data.platform is not Platform.TWITCH: return
        # -=-=- #
        self.twitch_viewers = data.status.get('live_viewers', self.twitch_viewers)
        self.twitch_live_state = data.status.get('live_state', self.twitch_live_state)
        if push: await self.update_status_change()

    async def on_youtube_status_change(self, data:ChatStatusChangeData, push:bool=True):
        if data.platform is not Platform.YOUTUBE: return
        # -=-=- #
        self.youtube_viewers = data.status.get('live_viewers', self.youtube_viewers)
        self.youtube_live_state = data.status.get('live_state', self.youtube_live_state)
        if push: await self.update_status_change()

