#! /usr/bin/env python3

# give the bot AI capabilities. 

"""
Single sentence description.

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

# from ...signals import EventBus, EventData, QueryBus, QueryData, Response

from pytchat import LiveChatAsync, ChatDataFinished
from pytchat.processors.default.processor import Chatdata
import asyncio
import httpx
from datetime import datetime


from dataclasses import dataclass, field
import enum
from typing import Any, Callable

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

from .chat import MessageOutData, Platform

# -=-=- Functions & Classes -=-=- #

class ReusableAsyncClient(httpx.AsyncClient):
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

# -=-=- Config Class -=-=- #

@configclass
class YouTubeConfig(ConfigClass):
    video_id:str = ""

# -=-=- Data Classes -=-=- #

@dataclass
class SetYouTubeIDData(EventData):
    video_id:str


@dataclass
class YouTubeChatMessageData(EventData):
    timestamp:datetime
    message:str
    user:str
    user_id:str
    amount:str = ""
    has_broadcaster:bool = False
    has_mod:bool = False
    has_vip:bool = False
    badge_url:str = ""
    emotes:list[dict[str, str]]=field(default_factory=list)


# -=-=- Service Class -=-=- #

@serviceclass("youtube")
class YouTubeService(BaseService[YouTubeConfig]):
    """"""
    livechat_client:ReusableAsyncClient = ReusableAsyncClient(http2=True)
    livechat:LiveChatAsync

    event_bus:EventBus = EventBus.get_instance()

    async def start(self):
        print(f"Starting YouTube Service")
        self.new_livechat(self.config.video_id)
        # self.new_livechat(self.config.video_id)

    async def stop(self):
        print("Stopping YouTube Service")
        if self.livechat is not None and self.livechat.is_alive():
            self.livechat.terminate()
        # -=-=- #
        try:
            self.livechat.raise_for_status()
        except ChatDataFinished:
            print("Chat data finished.")
        except Exception as e:
            print(type(e), str(e))
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register("SetYouTubeID", self.event_set_youtube_id)
        event_bus.register("MessageOut", self.event_message_out)
        
    def __register_queries__(self, query_bus):
        query_bus.register(
            'GetYouTubeID', 
            QueryBus.lambda_handler(lambda _: Response(self.config.video_id, video_id=self.config.video_id))
        )
        pass

    # -=-=- #

    def new_livechat(self, id:str) -> LiveChatAsync:
        print(f"Starting YouTube Livechat on ID: {id}")
        livechat = self.livechat = LiveChatAsync(
            id,
            # interruptable=False,
            client=self.livechat_client,
            callback=self.chat_callback
        )
        return livechat

    async def chat_callback(self, data:Chatdata):
        for chat in data.items:
            await self.youtube_chat_callback(chat)
            await data.tick_async() # AWK

    async def youtube_chat_callback(self, data):
        print(f"{data.datetime} [{data.author.name}]-{data.message} {data.amountString}")
        user:str = data.author.name
        if user.startswith('@'): user = user[1:]
        # replace with dedicated function and store them incase missing (happens)
        emotes:list=data.messageEx
        if isinstance(emotes[0], str): emotes=[]
        # -=-=- #
        await self.event_bus.emit("YouTubeChatMessage", YouTubeChatMessageData(
            timestamp=data.datetime,
            message=data.message,
            user=user,
            user_id=data.author.channelId,
            amount=data.amountString,
            # -=-=- #
            has_broadcaster=data.author.isChatOwner,
            has_mod=data.author.isChatModerator,
            has_vip=data.author.isChatSponsor,
            emotes=emotes,
        ))

    # TODO - add functionality here

    # -=-=- Events -=-=- #

    async def event_message_out(self, data:"MessageOutData"):
        if data.platform is not Platform.YOUTUBE: return
        # -=-=- #
        print("Youtube Message sending isn't available at this time.")

    async def event_set_youtube_id(self, data:SetYouTubeIDData):
        print(f"Setting Youtube ID to {data.video_id}")
        self.config.video_id = data.video_id
        self.new_livechat(self.config.video_id)

    # TODO - add event handlers here


# EOF #
