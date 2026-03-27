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
from streambot.core.decorators import throttle

from .chat import ChatMessageOutData, Platform, LiveState, ChatStatusChangeData
from .tick import OnTickData

import emojis
# import dismoji

import re
import json
import urllib

# -=-=- Functions & Classes -=-=- #

def pytchat_exception_handler(
    loop: asyncio.AbstractEventLoop,
    context: dict[str, Any],
) -> None:
    exc = context.get("exception")

    if isinstance(exc, asyncio.CancelledError):
        return

    loop.default_exception_handler(context)

def parse_timestamp(timestamp:str) -> int:
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp() * 1000)

class ReusableAsyncClient(httpx.AsyncClient):
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

async def get_youtube_data_unsafe(video_id: str) -> dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        html = resp.text

    resp = {}

    # Extract the JSON blob from the HTML
    json_match = re.search(r'var ytInitialData = ({.*?});</script>', html, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(1))

        # Recursive search function
        def find_view_count(obj, path="root"):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}['{k}']"
                    if k == "viewCount" and "runs" in v and len(v["runs"]) > 0:
                        return current_path, v["runs"][0]["text"]
                    result = find_view_count(v, current_path)
                    if result:
                        return result
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    result = find_view_count(item, current_path)
                    if result:
                        return result
            return None

        result = find_view_count(data)
        if result:
            path, live_viewers = result
            # print("Path to viewCount:", path)
            # print("LIVE VIEWERS:", count)
            # -=-=- #
            # Get the actual number
            if 'waiting' in live_viewers:
                live_viewers = live_viewers.replace('waiting', '').strip()
                resp['live_state'] = LiveState.OFFLINE
            if 'watching' in live_viewers:
                resp['live_state'] = LiveState.ONLINE
                live_viewers = live_viewers.replace('watching', '').replace('now', '').strip()
            # print(f'Json match: {live_viewers}')
            if live_viewers: resp['live_viewers'] = int(live_viewers.replace(',',''))
        else:
            # print("viewCount not found")
            pass

    return resp

async def get_youtube_data(video_id: str) -> dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        html = resp.text
    # -=-=- #
    resp = {}
    resp_unsafe = await get_youtube_data_unsafe(video_id)
    # -=-=- #
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        return {**resp_unsafe, "live_state": LiveState.OFFLINE, "live_viewers": 0}
    # -=-=- #
    data = json.loads(match.group(1))
    microformat = data.get("microformat", {}).get("playerMicroformatRenderer", {})
    is_live = microformat.get("liveBroadcastDetails", {}).get("isLiveNow", False)
    is_upcoming = microformat.get("liveBroadcastDetails", {}).get("isUpcoming", False)
    # -=-=- #
    if is_upcoming: resp['live_state'] = LiveState.OFFLINE
    if is_live: resp['live_state'] = LiveState.ONLINE
    # -=-=- #
    return {**resp_unsafe, **resp}



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
    timestamp:int
    message:str
    user:str
    user_id:str
    amount:str = ""
    has_broadcaster:bool = False
    has_mod:bool = False
    has_ads:bool = True
    badge_url:str = ""
    emotes:dict[str, str]=field(default_factory=dict)

@dataclass
class UpdateViewersYoutubeData(EventData):
    viewers:int


# -=-=- Service Class -=-=- #

@serviceclass("youtube")
class YouTubeService(BaseService[YouTubeConfig]):
    """"""
    livechat_client:ReusableAsyncClient = ReusableAsyncClient(http2=True)
    livechat:LiveChatAsync

    event_bus:EventBus = EventBus.get_instance()

    emotes:dict[str, str] = {}

    # -=-=- #

    live_state:LiveState = LiveState.CONNECTING
    viewers:int = 0

    async def start(self):
        print(f"Starting YouTube Service")
        self.new_livechat(self.config.video_id)
        # self.new_livechat(self.config.video_id)
        await self.poll_data()

    async def stop(self):
        print("Stopping YouTube Service")
        if self.livechat is not None and self.livechat.is_alive():
            self.livechat.terminate()
            self.livechat.listen_task.cancel()
        # -=-=- #
        try:
            self.livechat.raise_for_status()
        except ChatDataFinished:
            print("Chat data finished.")
        except Exception as e:
            pass
            # print(type(e), str(e))
        print("YouTube Stopped.")
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register("SetYouTubeID", self.event_set_youtube_id)
        event_bus.register("ChatMessageOut", self.event_chat_message_out)
        
        event_bus.register("OnHalfMinuteTick", self.event_on_tick)
        # self.register("OnFiveMinuteTick", self.on_long_tick)
        
    def __register_queries__(self, query_bus):
        query_bus.register(
            'GetYouTubeID', 
            QueryBus.lambda_handler(lambda _: Response(self.config.video_id, video_id=self.config.video_id))
        )

        query_bus.register('GetYouTubeViewers', self.query_get_youtube_viewers)
        query_bus.register('GetYouTubeLiveState', self.query_get_youtube_live_state)

    # -=-=- #

    @throttle(10)
    async def poll_data(self):
        data = await get_youtube_data(self.config.video_id)
        # -=-=- #
        self.viewers = data.get('live_viewers', self.viewers)
        self.live_state = data.get('live_state', self.live_state)
        status = {'live_state':self.live_state, **data}
        await self.event_bus.emit(f"ChatStatusChangeEvent", ChatStatusChangeData(platform=Platform.YOUTUBE, status=status))

    # -=-=- #

    def new_livechat(self, id:str) -> LiveChatAsync:
        print(f"Starting YouTube Livechat on ID: {id}")
        livechat = self.livechat = LiveChatAsync(
            id,
            interruptable=False,
            client=self.livechat_client,
            callback=self.chat_callback,
            exception_handler=pytchat_exception_handler

        )
        if livechat.is_replay(): livechat.terminate()
        return livechat

    async def chat_callback(self, data:Chatdata):
        if self.livechat.is_replay(): return
        # -=-=- #
        for chat in data.items:
            await self.youtube_chat_callback(chat)
            await data.tick_async() # AWK

    async def youtube_chat_callback(self, data):
        # print(f"{data.datetime} [{data.author.name}]-{data.message} {data.amountString}")
        user:str = data.author.name
        msg:str = data.message
        # msg:str = emojis.encode(data.message)
        if user.startswith('@'): user = user[1:]
        # replace with dedicated function and store them incase missing (happens)
        emotes:dict[str, str]=self.parse_emotes(msg, data.messageEx)
        # -=-=- #
        await self.event_bus.emit("YouTubeChatMessage", YouTubeChatMessageData(
            timestamp=parse_timestamp(data.datetime),
            message=msg,
            user=user,
            user_id=data.author.channelId,
            amount=data.amountString,
            # -=-=- #
            has_broadcaster=data.author.isChatOwner,
            has_mod=data.author.isChatModerator,
            has_ads=not data.author.isChatSponsor,
            emotes=emotes,
        ))

    def parse_emotes(self, msg:str, emotes:list[dict[str, str]]) -> dict[str, str]:
        if isinstance(emotes[0], str): emotes=[]
        # -=-=- #
        found = {}
        for emote in emotes:
            if 'txt' not in emote or emote['txt'] == '':
                print("weird emote found!!!", emote)
                continue
            if emote['txt'] not in self.emotes:
                self.emotes[emote['txt']] = emote['url']
        for emote in self.emotes:
            if emote in msg:
                found[emote]=self.emotes[emote]
        return found
    
    # -=-=- #

    # async def update_view_count(self):
    #     viewers = await get_youtube_live_viewers(self.config.video_id)
    #     if viewers: await self.event_bus.emit("UpdateViewersYoutube", UpdateViewersYoutubeData(viewers=viewers))

    # -=-=- Events -=-=- #

    async def event_on_tick(self, _:OnTickData):
        await self.poll_data()

    async def event_chat_message_out(self, data:"ChatMessageOutData"):
        if data.platform is not Platform.YOUTUBE: return
        # -=-=- #
        print("Youtube Message sending isn't available at this time.")

    async def event_set_youtube_id(self, data:SetYouTubeIDData):
        print(f"Setting Youtube ID to {data.video_id}")
        self.config.video_id = data.video_id
        self.viewers = 0
        self.live_state = LiveState.CONNECTING
        self.new_livechat(self.config.video_id)
        await self.poll_data()

    async def query_get_youtube_viewers(self, _:QueryData) -> Response:
        await self.poll_data()
        return Response(self.viewers, viewers=self.viewers)
    
    async def query_get_youtube_live_state(self, _:QueryData) -> Response:
        await self.poll_data()
        return Response(self.live_state, live_state=self.live_state)


# EOF #
