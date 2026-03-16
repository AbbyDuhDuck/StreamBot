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
from dataclasses import dataclass
from typing import Any, Callable
from datetime import datetime

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_youtube import YouTubeChatMessageData


# -=-=- Functions & Classes -=-=- #

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
    timestamp:datetime|None = None
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False
    # user
    has_broadcaster:bool = False
    has_head_mod:bool = False
    has_mod:bool = False
    has_vip:bool = False
    has_ads:bool = True
    user_color: str = "#ccc"

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
        print(data.emotes)
        await self.event_bus.emit("ChatMessage", ChatMessageData(
            message=data.message,
            user=data.user,
            timestamp=data.timestamp,
            platform=Platform.YOUTUBE,
            has_broadcaster=data.has_broadcaster,
            has_mod=data.has_mod,
            has_vip=data.has_vip
            # TODO: emotes
        ))

    # TODO - add event handlers here


# EOF #
