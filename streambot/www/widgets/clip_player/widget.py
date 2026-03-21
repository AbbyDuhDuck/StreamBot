#! /usr/bin/env python3

"""Chat widget for the WebUI."""

from dataclasses import dataclass
import random
from typing import Any

from streambot.service.builtin.chat_youtube import UpdateViewersYoutubeData
from streambot.service.builtin.chat_twitch import TwitchChannelQueryData, TwitchEventData, TwitchClipQueryData, TwitchQueryResponse
from streambot.service.builtin.sound import PlayTTSData
from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, ChatMessageOutData, MessageLevel, Platform, UserType
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals import EventBus, EventData, QueryBus, Response

from twitchAPI.object.eventsub import ChannelRaidEvent, ChannelAdBreakBeginEvent
from twitchAPI.twitch import Clip

import asyncio
from functools import wraps


@dataclass
class ClipPlayerData:
    clip:str|None = None
    url:str|None = None
    channel:str|None = None

class Widget(base.Widget):
    name = "clip_player"
    display_name = "Clip Player"
    description = "plays twitch clips (youtube shorts?)"

    active = True

    event_bus: EventBus | None = EventBus.get_instance()
    query_bus: QueryBus | None = QueryBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    sent_clips:dict[str, dict[str, Any]] = {}
    

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.register("WSMessageClip", self.event_ws_message)

        self.register("ChatMessage", self.event_chat_message)
        self.register("ClipPlayerSendClip", self.event_send_clip)
        self.register("ClipPlayerSendRandomClip", self.event_random_send_clip)

    def register_queries(self, query_bus):
        self.query_bus = query_bus

    # -=-=- #

    async def say(self, message:str):
        await self.event_bus.emit('PlayTTS', PlayTTSData(message))

    async def msg(self, message:str, user_type:UserType=UserType.BOT, platform:Platform=Platform.TWITCH):
        await self.event_bus.emit("ChatMessageOut", ChatMessageOutData(message, user_type=user_type, platform=platform))

    async def out(self, message:str, level:MessageLevel=MessageLevel.INFO):
        await self.event_bus.emit("ChatNotification", ChatNotificationData(message, level))

    # -=-=- #

    async def event_ws_message(self, event:WSMessageData):
        print(f"Player Received WSMessage ({event.event}): {event.data}")

        if event.event == 'send-random-clip':
            await self.event_bus.emit("ClipPlayerSendRandomClip", ClipPlayerData(channel=event.data.get('user')))

    # -=-=- #
    
    async def send_clip(self, data:dict[str, Any]):
        print('sending clip:', data)
        self.sent_clips[data.get('id', None)] = data
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="clip", event='send-clip', message=data))

    # -=-=- #
    
    # async def update_count(self):
    #     await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="counter", event='update', message={
    #         'counter-count': self.count,
    #     }))

    # -=-=- #

    async def get_random_clip_data(self, channel:str) -> dict[str, str]|None:
        clip: Clip|None = (await self.query_bus.query("GetTwitchRandomClipData", TwitchChannelQueryData(channel=channel))).get()
        if clip is None: return None
        # -=-=- #
        return {
            **clip.to_dict()
        }

    async def get_clip_data(self, url:str=None, clip:str=None) -> dict[str, str]|None:
        clip: Clip|None = (await self.query_bus.query("GetTwitchClipData", TwitchClipQueryData(url=url, clip=clip))).get()
        if clip is None: return None
        # -=-=- #
        return {
            **clip.to_dict()
        }

    # -=-=- #

    def context(self):
        return {
            'clip_list': [*self.sent_clips.values()],
        }
    
    # -=-=- Events -=-=- #

    async def event_chat_message(self, data:ChatMessageData):
        if data.platform is not Platform.TWITCH: return
        print(f"{data.user}// {data.message}")
        clip_link = "https://www.twitch.tv/littlefaerii/clip/CautiousBeautifulHeronArsonNoSexy-RXerO7i80AwfYata"
        clip_id = "CautiousBeautifulHeronArsonNoSexy-RXerO7i80AwfYata"
        channel_id = "littlefaerii"
        # await self.event_bus.emit("ClipPlayerSendClip", ClipPlayerData(url=clip_link, clip=clip_id))
        # await self.event_bus.emit("ClipPlayerSendRandomClip", ClipPlayerData(channel=channel_id))

    async def event_random_send_clip(self, data:ClipPlayerData):
        clip = await self.get_random_clip_data(data.channel)
        print(clip)
        if clip is None: return await self.out(f'Cannot find clip for channel: {data.channel}', MessageLevel.WARNING)
        # -=-=- #
        await self.send_clip(clip)

    async def event_send_clip(self, data:ClipPlayerData):
        clip = await self.get_clip_data(data.url)
        print(clip)
        if clip is None: return await self.out(f'Cannot find clip: {data.url}', MessageLevel.WARNING)
        # -=-=- #
        await self.send_clip(clip)

