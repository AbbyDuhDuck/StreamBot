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
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

from .tick import OnTickData
from .chat import ChatMessageData, Platform, ChatNotificationData, NotifType
from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

# -=-=- #

import logging
from pprint import pprint, pformat
from typing import Dict, List, override, Type

import requests
from twitchAPI.helper import first, build_url, TWITCH_API_BASE_URL
from twitchAPI.twitch import Twitch, TwitchUser, CustomReward, Stream, Video, ChannelInformation, VideoType

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelFollowEvent
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper

from twitchAPI.eventsub.webhook import EventSubWebhook
# from twitchAPI.eventsub.base import EventSubBase
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent, ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.object.eventsub import ChannelUpdateEvent
from twitchAPI.object import eventsub
from twitchAPI.type import AuthScope, ChatEvent, TwitchAPIException
from twitchAPI import chat # import Chat, EventData, ChatMessage, ChatSub, ChatCommand
# from twitchAPI.pubsub import PubSub
# import asyncio
# import secret

import time
from datetime import datetime, timedelta

from uuid import UUID

from threading import Thread

from dataclasses import dataclass
from typing import Generic, TypeVar

# from . import ChatService, ChatSettings

# -=-=- Setup webbrowser -=-=- #

import webbrowser
CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
OPERA_PATH="C:\\Users\\abbyd\\AppData\\Local\\Programs\\Opera\\opera.exe"
OPERAGX_PATH="C:\\Users\\abbyd\\AppData\\Local\\Programs\\Opera GX\\opera.exe"
webbrowser.register('chrome', None, webbrowser.GenericBrowser([CHROME_PATH, "--incognito", "%s"]))
webbrowser.register('opera', None, webbrowser.GenericBrowser([OPERA_PATH, "--private", "%s"]))
webbrowser.register("operaGX", None, webbrowser.GenericBrowser([OPERAGX_PATH, "--private", "%s"]), preferred=True)

# -=-=- Globals -=-=- #

# APP_ID = secret.twitch.APP_ID
# APP_SECRET = secret.twitch.APP_SECRET
# USER_SCOPE = [
#     AuthScope.CHAT_READ, AuthScope.CHAT_EDIT,
#     AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.BITS_READ, AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
#     AuthScope.MODERATOR_READ_FOLLOWERS, AuthScope.MODERATOR_MANAGE_SHOUTOUTS, AuthScope.CHANNEL_MANAGE_RAIDS,
# ]

# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #

@configclass
class TwitchConfig(ConfigClass):
    app_id:str = None
    app_secret:str = None
    account_user:str = None
    account_bot:str = None
    token_path:str = "./usr/secret/TOKEN_{type}_{user}.js"
    user_scope:list[AuthScope] = field(default_factory=lambda: [
        AuthScope.CHAT_READ, AuthScope.CHAT_EDIT,
        AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.BITS_READ, AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
        AuthScope.MODERATOR_READ_FOLLOWERS, AuthScope.MODERATOR_MANAGE_SHOUTOUTS, AuthScope.CHANNEL_MANAGE_RAIDS,
    ])

# -=-=- Data Classes -=-=- #

@dataclass
class SetGameData(EventData):
    game:str

@dataclass
class TwitchChatMessageData(EventData):
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
    emotes:dict[str, str] = field(default_factory=lambda: dict)
    data:chat.ChatMessage = field(default_factory=lambda: None)

@dataclass
class UpdateViewersTwitchData(EventData):
    viewers:int

# -=-=- #

T = TypeVar("T")

@dataclass
class TwitchEventData(EventData, Generic[T]):
    event:str
    data:T



# -=-=- Service Class -=-=- #

@serviceclass("twitch")
class TwitchService(BaseService[TwitchConfig]):
    # -=-=- #
    twitch_user: Twitch = None
    twitch_bot: Twitch = None
    # -=-=- #
    user_data: Dict[str, TwitchUser] = {}
    chat_user: chat.Chat = None
    chat_bot: chat.Chat = None
    eventsub: EventSubWebsocket = None
    # -=-=- #
    auth_done:bool = False
    _is_stopping:bool = False
    # -=-=- #
    event_bus:EventBus = EventBus.get_instance()

    async def start(self):
        print(f"Starting Twitch Service")
        # -=-=- #
        await self._auth()
        # -=-=- #
        await self._start_bots()
        await self._start_events()

    async def stop(self):
        print("Stopping Twitch Service")
        # -=-=- #
        self._is_stopping = True
        # -=-=- #
        if self.chat_user: self.chat_user.stop()
        if self.chat_bot: self.chat_bot.stop()
        if self.eventsub: await self.eventsub.stop()
        # -=-=- #
        if self.twitch_user: await self.twitch_user.close()
        if self.twitch_bot: await self.twitch_bot.close()
        # -=-=- #
        print('Twitch Stopped')

    # -=-=- #

    async def out(self, message:str, _type:NotifType=NotifType.INFO):
        await self.event_bus.emit("ChatNotification", ChatNotificationData(message=message, type=_type))

    # -=-=- #

    async def _auth(self):
        await self._auth_user()
        await self._auth_bot()
        await self._auth_app()
        self.auth_done = True
        print("auth done")

    def get_token_path(self, type:str, user:str):
        return self.config.token_path.format(type=type, user=user)

    async def _auth_user(self):
        if self.config.account_user is None: return
        # -=-=- #
        print("Auth User")
        # set up twitch api instance and add user authentication with some scopes
        self.twitch_user = twitch = await Twitch(self.config.app_id, self.config.app_secret)
        helper = UserAuthenticationStorageHelper(twitch, self.config.user_scope, self.get_token_path("USER", self.config.account_user))
        await helper.bind()

    async def _auth_bot(self):
        if self.config.account_bot is None: return
        # -=-=- #
        print("Auth Bot")
        # set up twitch api instance and add user authentication with some scopes
        self.twitch_bot = twitch = await Twitch(self.config.app_id, self.config.app_secret)
        helper = UserAuthenticationStorageHelper(twitch, self.config.user_scope, self.get_token_path("BOT", self.config.account_bot))
        await helper.bind()

    async def _auth_app(self):
        print("Auth App")
        # Initialize Twitch instance
        self.twitch_app = twitch = await Twitch(self.config.app_id, self.config.app_secret)
        # Get App token
        token = twitch.get_app_token()
        # Set App token
        await twitch.set_app_authentication(token, scope=[
            AuthScope.CHAT_READ,
            AuthScope.CHAT_EDIT,
            AuthScope.USER_WRITE_CHAT,  # required for for_source_only messages
        ])
        # print("App token acquired:", self.twitch_app.get_used_token())

    # -=-=- #

    async def _start_bots(self):
        if self.config.account_user is None: return
        # -=-=- #
        print("Connecting user to Twitch Chat.")
        self.chat_user = await self._chat_start(self.twitch_user, self.config.account_user)
        # -=-=-=- #
        if self.config.account_bot is None: return
        # -=-=- #
        print("Connecting bot to Twitch Chat.")
        self.chat_bot = await self._chat_start(
            self.twitch_bot, self.config.account_user,
            on_message=self.chatevent_on_message,
            on_ready=self.chatevent_on_ready,
        )
        pass

    async def _chat_start(self, twitch:Twitch, channel:str, 
            on_message=None, on_ready=None
        ) -> chat.Chat:
        if not self.auth_done:
            print("Cannot start Twitch chat as the auth service is not complete.")
        # -=-=- #
        # create chat instance
        _chat = await chat.Chat(twitch, no_shared_chat_messages=False)
        _chat.start()
        # listen to when the bot is done starting up and ready to join channels
        async def event_join_channel(event: EventData):
            await _chat.join_room(channel)
            if on_ready is not None: await on_ready(event)
        _chat.register_event(ChatEvent.READY, event_join_channel)
        # listen to chat messages
        if on_message is not None:
            _chat.register_event(ChatEvent.MESSAGE, on_message)

        return _chat

    async def _start_events(self):
        if not self.auth_done:
            print("Cannot start Twitch eventsub as the auth service is not complete.")
        # -=-=- #
        print("Connecting to Twitch EventSub.")
        
        # create eventsub websocket instance and start the client.
        self.eventsub = eventsub = EventSubWebsocket(self.twitch_user)
        eventsub.start()

        user_id = await self.get_user_id(self.config.account_user)

        await eventsub.listen_stream_online(user_id, self.make_chat_event("StreamOnline"))
        await eventsub.listen_stream_offline(user_id, self.make_chat_event("StreamOffline"))

        # await eventsub.listen_channel_ad_break_begin(user_id, _display_args("Ads Start"))

        await eventsub.listen_channel_bits_use(user_id, self.make_chat_event("BitsUsed"))

        await eventsub.listen_channel_subscribe(user_id, self.make_chat_event("Subscribe"))
        # await eventsub.listen_channel_subscription_end(user_id, self.make_chat_event("Subscribe End"))
        await eventsub.listen_channel_subscription_gift(user_id, self.make_chat_event("SubscribeGift"))
        # await eventsub.listen_channel_subscription_message(user_id, self.make_chat_event("Subscribe Message"))

        await eventsub.listen_channel_raid(self.make_chat_event("Raid"), user_id)
        # await eventsub.listen_channel_raid(self.make_chat_event("RaidOut"), None, user_id)

        await eventsub.listen_channel_follow_v2(user_id, user_id, self.make_chat_event("Follow"))
        
        await eventsub.listen_channel_points_custom_reward_redemption_add(user_id, self.make_chat_event("Redeem"))
        

    # -=-=- #

    def make_chat_event(self, event:str) -> Coroutine:
        async def chat_event(event_data):
            print(f"Triggering event: {event}")
            await self.event_bus.emit(f"Twitch{event}Event", TwitchEventData(event=event, data=event_data))
        return chat_event

    # -=-=- #

    async def chatevent_on_ready(self, event:chat.EventData):
        print("Twitch Started")
        # TODO: emit twitch started event

    async def chatevent_on_message(self, message:chat.ChatMessage):
        # print(f"message by {message.user.display_name} from {message.room.name} chat")
        # print(f"Shared Chat Message (maybe): {message.source_room_id != message.room.room_id}")
        # -=-=- #
        has_paid = message.user.subscriber or message.user.turbo
        if message.user.user_type: print(message.user.user_type)
        # -=-=- #
        await self.event_bus.emit("TwitchChatMessage", TwitchChatMessageData(
            message=message.text,
            user=message.user.display_name,
            timestamp=message.sent_timestamp,
            platform=Platform.TWITCH,
            # shared_chat=False,
            has_broadcaster=message.user.name==self.config.account_user.lower(),
            # has_head_mod=,
            has_mod=message.user.mod,
            has_vip=message.user.vip,
            has_ads=not has_paid,
            user_color=message.user.color,
            data=message,
            emotes=self.parse_emotes(message.text, message.emotes)
        ))

    def parse_emotes(self, msg:str, emotes:dict[str, list[dict[str, str]]]|None) -> dict[str, str]:
        if emotes is None: return {}
        return {msg[int(emotes[id][0]['start_position']) : int(emotes[id][0]['end_position'])+1] : id for id in emotes}

    # -=-=- #

    def __register_events__(self, event_bus):
        self.event_but = event_bus

        event_bus.register("TwitchRedeemEvent", self.event_on_redeem)
        
    def __register_queries__(self, query_bus):
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )

        query_bus.register("GetTwitchViewers", self.query_get_twitch_viewers)

    # -=-=- #

    async def get_user(self, channel:str, force:bool=False) -> TwitchUser:
        if channel not in self.user_data:
            self.user_data[channel] = await first(self.twitch_user.get_users(logins=[channel]))
        return self.user_data[channel]
    
    async def get_user_id(self, channel:str, force:bool=False) -> str:
        user = await self.get_user(channel, force)
        if user: return user.id
    
    async def get_stream_data(self, channel:str) -> Stream:
        user_id = await self.get_user_id(channel)
        if user_id: return await first(self.twitch_user.get_streams(user_id=[user_id]))
    
    async def get_last_vod_data(self, channel:str) -> Video:
        user_id = await self.get_user_id(channel)
        if user_id: return await first(self.twitch_user.get_videos(user_id=[user_id], video_type=VideoType.ARCHIVE))

    async def get_channel_data(self, channel:str) -> ChannelInformation:
        # self.twitch_user.get_channel_information()
        user_id = await self.get_user_id(channel)
        if user_id: return (await self.twitch_user.get_channel_information(broadcaster_id=[user_id]))[0]

    # -=-=- #

    # async def update_view_count(self):
    #     stream = await self.get_stream_data(self.config.account_user)
    #     view_count = stream is not None and stream.viewer_count or 0
    #     await self.event_bus.emit("UpdateViewersTwitch", UpdateViewersTwitchData(viewers=view_count))

    # -=-=- Events -=-=- #

    async def event_on_redeem(self, data:TwitchEventData[ChannelPointsCustomRewardRedemptionAddEvent]):
        redeem = data.data.event.reward.title
        usr_in = data.data.event.user_input
        user = data.data.event.user_name
        print(f"{user} redeemed {redeem} : {usr_in}")
        await self.out(f"{user} redeemed {redeem} : {usr_in}")

        redeem_id = ''
        remove_word = ['a', 'an', 'the']
        remove_char = "!?'"
        for word in redeem.split():
            if word in remove_word: continue        
            redeem_id += word.title()
        for ch in remove_char:
            redeem_id = redeem_id.replace(ch, '')

        await self.event_bus.emit(f"On{redeem_id}Redeem", data)

    
    async def query_get_twitch_viewers(self, _:QueryData) -> Response:
        stream = await self.get_stream_data(self.config.account_user)
        viewers = stream is not None and stream.viewer_count or 0
        return Response(viewers, viewers=viewers)


# EOF #
