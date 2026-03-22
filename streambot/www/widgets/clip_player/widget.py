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
    stay:bool = False

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
        
        self.register("ClipPlayerPlayClip", self.event_play_clip)
        self.register("ClipPlayerStopClip", self.event_stop_clip)

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
        if event.event == 'play-pressed':
            await self.event_bus.emit("ClipPlayerPlayClip", ClipPlayerData(clip=event.data.get('id'), stay=event.data.get('stay', False)))
        if event.event == 'clear-clip':
            await self.clear_clip(event.data.get('id'))

    # -=-=- #
    
    async def send_clip(self, data:dict[str, Any]):
        print('playing clip:', data.get('title', 'Title Not Found'))
        self.sent_clips[data.get('id', None)] = data
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="clip", event='send-clip', message=data))

    async def clear_clip(self, id:str|None):
        if id is None: return
        if id in self.sent_clips: del(self.sent_clips[id])
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="clip", event='clear-clip', message={'id':id}))

    # -=-=- #

    async def play_clip(self, data:dict[str, Any]):
        print('playing clip:', data.get('title', 'Title Not Found'))
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="clip", event='play-clip', message=data))

    async def stop_clip(self, id:str|None):
        if id is None: return
        print('stopping clip:', id)
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="clip", event='stop-clip', message={'id':id}))

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
        # print(f"{data.user}// {data.message}")
        clip_link = "https://www.twitch.tv/littlefaerii/clip/CautiousBeautifulHeronArsonNoSexy-RXerO7i80AwfYata"
        clip_id = "CautiousBeautifulHeronArsonNoSexy-RXerO7i80AwfYata"
        channel_id = "littlefaerii"
        # await self.event_bus.emit("ClipPlayerSendClip", ClipPlayerData(url=clip_link, clip=clip_id))
        # await self.event_bus.emit("ClipPlayerSendRandomClip", ClipPlayerData(channel=channel_id))

    async def event_random_send_clip(self, data:ClipPlayerData):
        clip = await self.get_random_clip_data(data.channel)
        if clip is None: return await self.out(f'Cannot find clip for channel: {data.channel}', MessageLevel.WARNING)
        # -=-=- #
        await self.send_clip(clip)

    async def event_send_clip(self, data:ClipPlayerData):
        clip = await self.get_clip_data(data.url, data.clip)
        if clip is None: return await self.out(f'Cannot find clip: {data.url}', MessageLevel.WARNING)
        # -=-=- #
        await self.send_clip(clip)

    async def event_play_clip(self, data:ClipPlayerData):
        clip = await self.get_clip_data(data.url, data.clip)
        if clip is None: return await self.out(f'Cannot find clip: {data.url}', MessageLevel.WARNING)
        # -=-=- #
        await self.play_clip(clip)

    async def event_stop_clip(self, data:ClipPlayerData):
        clip_id = data.clip or data.url.split('?')[0].split('/')[-1]
        await self.stop_clip(clip_id)
