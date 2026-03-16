#! /usr/bin/env python3

# give the bot AI capabilities. 

"""
Acts as a mixin for all that chat services

This package provides functionality for... [TODO - add description] 

Modules & Subpackages:
----------------------
- TODO

Usage:
------
TODO
"""

# -=-=- Imports & Globals -=-=- #

from enum import Enum
from dataclasses import dataclass, field
import hashlib
from typing import Any, Callable
from datetime import datetime

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio
import random


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_youtube import YouTubeChatMessageData
    from .chat_twitch import TwitchChatMessageData


USER_COLORS = [
    "#FF595E",  # red
    "#FF924C",  # orange
    "#FFCA3A",  # yellow
    "#8AC926",  # lime
    "#52B788",  # green
    "#2EC4B6",  # teal
    "#00BBF9",  # sky blue
    "#3A86FF",  # blue
    "#4361EE",  # royal blue
    "#8338EC",  # purple
    "#9D4EDD",  # violet
    "#C77DFF",  # lavender purple
    "#F72585",  # magenta
    "#FF4D8D",  # pink
    "#FF6F91",  # rose
    "#F15BB5",  # hot pink
    "#06D6A0",  # aqua green
    "#00F5D4",  # bright aqua
    "#4CC9F0",  # cyan
    "#90DBF4",  # light cyan
    "#B8F2E6",  # mint
    "#80ED99",  # bright green
    "#C7F464",  # yellow-green
    "#FFD166",  # gold
    "#F4A261",  # warm orange
    "#E76F51",  # coral
    "#FF006E",  # neon magenta
    "#B5179E",  # deep magenta
    "#7209B7",  # deep purple
    # "#560BAD",  # indigo
]

# -=-=- Functions & Classes -=-=- #

def get_random_user_color(user:str) -> str:
    seed = int(hashlib.sha256(user.encode()).hexdigest(), 16)
    rand = random.Random(seed)
    return rand.choice(USER_COLORS)


class Platform(Enum):
    TWITCH = "Twitch"
    YOUTUBE = "YouTube"
    DISCORD = "Discord"

class UserType(Enum):
    USER = "User"
    BOT = "Bot"

# -=-=- Config Class -=-=- #

@configclass
class ChatConfig(ConfigClass):
    pass


# -=-=- Data Classes -=-=- #

@dataclass
class ChatNotificationData(EventData):
    message:str

@dataclass
class ChatMessageData(EventData):
    # message
    message:str
    user:str
    timestamp:int|None = None
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False
    # user
    has_broadcaster:bool = False
    has_head_mod:bool = False
    has_mod:bool = False
    has_vip:bool = False
    has_ads:bool = True
    user_color: str = "#ccc"
    # raw
    data:EventData = None

@dataclass
class MessageOutData(EventData):
    message:str
    user_type:UserType = UserType.BOT
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False


# -=-=- Service Class -=-=- #

@serviceclass("chat")
class ChatService(BaseService[ChatConfig]):
    event_bus:EventBus = EventBus.get_instance()

    async def start(self):
        # print(f"Starting AI Service")
        pass

    async def stop(self):
        # print("Stopping AI Service")
        pass
    
    # -=-=- #

    def __register_events__(self, event_bus):
        self.event_bus = event_bus
        event_bus.register("YouTubeChatMessage", self.event_youtube_chat_message)
        event_bus.register("TwitchChatMessage", self.event_twitch_chat_message)
        pass
        
    def __register_queries__(self, query_bus):
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )
        pass

    # -=-=- #

    # TODO - add functionality here

    # -=-=- Events -=-=- #
    
    async def event_youtube_chat_message(self, data:"YouTubeChatMessageData"):
        print("YouTube Emotes", data.emotes)
        await self.event_bus.emit("ChatMessage", ChatMessageData(
            message=data.message,
            user=data.user,
            timestamp=data.timestamp,
            platform=Platform.YOUTUBE,
            has_broadcaster=data.has_broadcaster,
            has_mod=data.has_mod,
            has_ads=data.has_ads,
            data=data,
            user_color=get_random_user_color(data.user),
            # TODO: emotes
        ))

    async def event_twitch_chat_message(self, data:"TwitchChatMessageData"):
        print("Twitch emotes:", data.emotes)
        await self.event_bus.emit("ChatMessage", ChatMessageData(
            message=data.message,
            user=data.user,
            timestamp=data.timestamp,
            platform=Platform.TWITCH,
            has_broadcaster=data.has_broadcaster,
            has_head_mod=data.has_head_mod,
            has_mod=data.has_mod,
            has_vip=data.has_vip,
            has_ads=data.has_ads,
            user_color=data.user_color,
            data=data,
            # TODO: emotes
        ))

    # TODO - add event handlers here


# EOF #
