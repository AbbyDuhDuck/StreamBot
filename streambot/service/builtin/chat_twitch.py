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
import random
from typing import Any, Callable, Coroutine

from .tick import OnTickData
from .chat import ChatMessageData, Platform, UserType, ChatNotificationData, MessageLevel, LiveState, ChatStatusChangeData
from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

# -=-=- #

import logging
from pprint import pprint, pformat
from typing import Dict, List, override, Type

import requests
from twitchAPI.helper import first, build_url, TWITCH_API_BASE_URL
from twitchAPI.twitch import Twitch, TwitchUser, CustomReward, Stream, Video, ChannelInformation, VideoType, Clip, SharedChatSession

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelFollowEvent, ChatMessage
from twitchAPI.oauth import UserAuthenticator, UserAuthenticationStorageHelper

from twitchAPI.eventsub.webhook import EventSubWebhook
# from twitchAPI.eventsub.base import EventSubBase
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent, ChannelPointsCustomRewardRedemptionAddEvent, ChannelAdBreakBeginEvent
from twitchAPI.object.eventsub import ChannelUpdateEvent, ChannelChatNotificationEvent
from twitchAPI.object.eventsub import ChannelSharedChatBeginEvent, ChannelSharedChatEndEvent, ChannelSharedChatUpdateEvent
from twitchAPI.object import eventsub
from twitchAPI.type import AuthScope, ChatEvent, TwitchAPIException
from twitchAPI import chat
# from twitchAPI.pubsub import PubSub
# import asyncio
# import secret

import time
from datetime import datetime, timedelta

from uuid import UUID

from threading import Thread

from dataclasses import dataclass
from typing import Generic, TypeVar

from .chat import ChatMessageOutData, Platform

from streambot.core.decorators import throttle, queued

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

def is_channel_live(broadcaster_login, client_id, access_token) -> bool:
    url = f'https://api.twitch.tv/helix/streams?user_login={broadcaster_login}'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json().get('data', [])
        return len(data) > 0
    else:
        print(f"Error checking stream status: {response.status_code}, {response.text}")
        return False

# -=-=- Config Class -=-=- #

@configclass
class TwitchConfig(ConfigClass):
    app_id:str = None
    app_secret:str = None
    account_user:str = None
    account_bot:str = None
    token_path:str = "./usr/secret/TOKEN_{type}_{user}.js"
    user_scope:list[AuthScope] = field(default_factory=lambda: [
        AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.USER_READ_CHAT,
        AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.BITS_READ, AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
        AuthScope.MODERATOR_READ_FOLLOWERS, AuthScope.MODERATOR_MANAGE_SHOUTOUTS, AuthScope.CHANNEL_MANAGE_RAIDS,
        AuthScope.CHANNEL_MANAGE_ADS, AuthScope.CHANNEL_READ_ADS,
    ])
    # hopefully remove
    account_head_mod:str = None

# -=-=- Data Classes -=-=- #

@dataclass
class SetGameData(EventData):
    game:str

@dataclass
class TwitchChatMessageData(EventData):
    # message
    message:str
    user:str
    reply_user:str|None = None
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

@dataclass
class TwitchChannelQueryData(QueryData):
    channel:str
    force:bool=False

@dataclass
class TwitchClipQueryData(QueryData):
    url:str|None = None
    clip:str|None = None
    channel:str|None = None


# T = TypeVar("T")

class TwitchQueryResponse(Response, Generic[T]):
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
    viewers:int = 0
    live_state:LiveState = LiveState.CONNECTING
    # -=-=- #
    shared_chat:bool = False
    shared_chat_host:str|None = None
    shared_chat_participants:list[str] = []
    shared_chat_viewers:int = 0
    # -=-=- #
    event_bus:EventBus = EventBus.get_instance()

    async def start(self):
        print(f"Starting Twitch Service")
        # -=-=- #
        await self._auth()
        # -=-=- #
        await self._start_bots()
        await self._start_events()
        # -=-=- #
        await self.poll_shared_chat()
        await self.poll_data()

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

    async def out(self, message:str, _type:MessageLevel=MessageLevel.INFO):
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
            AuthScope.USER_READ_CHAT,
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

        await eventsub.listen_channel_ad_break_begin(user_id, self.make_chat_event("AdStart"))

        await eventsub.listen_channel_bits_use(user_id, self.make_chat_event("BitsUsed"))

        await eventsub.listen_channel_subscribe(user_id, self.make_chat_event("Subscribe"))
        await eventsub.listen_channel_subscription_end(user_id, self.make_chat_event("SubscribeEnd"))
        await eventsub.listen_channel_subscription_gift(user_id, self.make_chat_event("SubscribeGift"))
        await eventsub.listen_channel_subscription_message(user_id, self.make_chat_event("SubscribeMessage"))

        await eventsub.listen_channel_raid(self.make_chat_event("Raid"), user_id)

        await eventsub.listen_channel_follow_v2(user_id, user_id, self.make_chat_event("Follow"))
        
        await eventsub.listen_channel_points_custom_reward_redemption_add(user_id, self.make_chat_event("Redeem"))

        await eventsub.listen_channel_shared_chat_update(user_id, self.make_chat_event("SharedChatUpdate"))
        await eventsub.listen_channel_shared_chat_begin(user_id, self.make_chat_event("SharedChatBegin"))
        await eventsub.listen_channel_shared_chat_end(user_id, self.make_chat_event("SharedChatEnd"))

        await eventsub.listen_channel_chat_notification(user_id, user_id, self.make_chat_event("ChatNotification"))
        # await eventsub.listen_automod_message_hold(user_id, self.make_chat_event("AutomodHold"))
        
        # await eventsub.listen_channel_poll_progress(user_id, self.make_chat_event("PollProgress"))
        # await eventsub.listen_channel_poll_begin(user_id, self.make_chat_event("PollBegin"))
        # await eventsub.listen_channel_poll_end(user_id, self.make_chat_event("PollEnd"))

        # await eventsub.listen_channel_prediction_begin(user_id, self.make_chat_event("PredictionBegin"))
        # await eventsub.listen_channel_prediction_end(user_id, self.make_chat_event("PredictionEnd"))
        # await eventsub.listen_channel_prediction_lock(user_id, self.make_chat_event("PredictionLock"))
        # await eventsub.listen_channel_prediction_progress(user_id, self.make_chat_event("PredictionProgress"))

    # -=-=- #

    def make_chat_event(self, event:str) -> Coroutine:
        async def chat_event(event_data):
            print(f"Triggering event: {event}")
            await self.event_bus.emit(f"Twitch{event}Event", TwitchEventData(event=event, data=event_data))
        return chat_event

    # -=-=- #

    async def set_live_state(self, state:LiveState, push:bool=True):
        if self.live_state is state: return 
        # -=-=- #
        self.live_state = state
        status = {'live_state':self.live_state}
        if push: await self.event_bus.emit(f"ChatStatusChangeEvent", ChatStatusChangeData(platform=Platform.TWITCH, status=status))
        

    async def chatevent_on_ready(self, event:chat.EventData):
        print("Twitch Started")
        await self.set_live_state(LiveState.CONNECTED)

    async def chatevent_on_message(self, message:chat.ChatMessage):
        shared_chat = self.shared_chat and message.source_room_id != message.room.room_id
        has_broadcaster = message.user.name == (self.config.account_user or "").lower()
        has_head_mod = message.user.name == (self.config.account_head_mod or "").lower()
        has_paid = message.user.subscriber or message.user.turbo
        # -=-=- #
        await self.event_bus.emit("TwitchChatMessage", TwitchChatMessageData(
            message=message.text,
            user=message.user.display_name,
            reply_user=message.reply_parent_display_name,
            timestamp=message.sent_timestamp,
            platform=Platform.TWITCH,
            shared_chat=shared_chat,
            has_broadcaster=has_broadcaster,
            has_head_mod=has_head_mod,
            has_mod=message.user.mod,
            has_vip=message.user.vip,
            has_ads=not has_paid,
            user_color=message.user.color,
            data=message,
            emotes=self.parse_emotes(message.text, message.emotes)
        ))

        message.user.user_type
        if message.bits or 0 < 0:
            await self.event_bus.emit("TwitchMessageBitsUsedEvent", TwitchEventData(message, data=message))

    def parse_emotes(self, msg:str, emotes:dict[str, list[dict[str, str]]]|None) -> dict[str, str]:
        if emotes is None: return {}
        return {msg[int(emotes[id][0]['start_position']) : int(emotes[id][0]['end_position'])+1] : id for id in emotes}

    # -=-=- #

    def __register_events__(self, event_bus):
        self.event_but = event_bus

        event_bus.register("TwitchRedeemEvent", self.event_on_redeem)
        event_bus.register("TwitchAdStartEvent", self.event_on_ad_start)
        event_bus.register("ChatMessageOut", self.event_chat_message_out)

        event_bus.register("TwitchShoutoutUser", self.event_shoutout_user)
        event_bus.register("TwitchStartRaid", self.event_start_raid)
        event_bus.register("TwitchStopRaid", self.event_stop_raid)

        # event_bus.register("TwitchStreamOnlineEvent", self.event_on_redeem)
        # event_bus.register("TwitchStreamOfflineEvent", self.event_on_redeem)

        event_bus.register("TwitchSharedChatUpdateEvent", self.event_on_shared_chat_update)
        event_bus.register("TwitchSharedChatBeginEvent", self.event_on_shared_chat_begin)
        event_bus.register("TwitchSharedChatEndEvent", self.event_on_shared_chat_end)

        event_bus.register("TwitchChatNotificationEvent", self.event_chat_notification)
        
        event_bus.register("OnHalfMinuteTick", self.event_on_tick)
        # self.register("OnFiveMinuteTick", self.on_long_tick)
        

    def __register_queries__(self, query_bus):
        # -=-=- #
        def response(cb:Callable[..., Coroutine]):
            async def func(data:TwitchChannelQueryData):
                resp = await cb(channel=data.channel, force=data.force)
                return TwitchQueryResponse(resp, data=resp)
            return func
        def clip_response(cb:Callable[..., Coroutine]):
            async def func(data:TwitchClipQueryData):
                resp = await cb(**data.__dict__)
                return TwitchQueryResponse(resp, data=resp)
            return func

        query_bus.register("GetTwitchUser", response(self.get_user))
        query_bus.register("GetTwitchUserID", response(self.get_user_id))
        query_bus.register("GetTwitchStreamData", response(self.get_stream_data))
        query_bus.register("GetTwitchVODData", response(self.get_last_vod_data))
        query_bus.register("GetTwitchChannelData", response(self.get_channel_data))

        query_bus.register("GetTwitchViewers", self.query_get_twitch_viewers)
        query_bus.register("GetTwitchLiveState", self.query_get_twitch_live_state)
        query_bus.register("GetTwitchSharedChatState", self.query_get_shared_chat_state)

        query_bus.register("GetTwitchClipData", clip_response(self.get_clip_data))
        query_bus.register("GetTwitchRandomClipData", response(self.get_random_clip_data))

    # -=-=- #

    async def get_user(self, channel:str, force:bool=False) -> TwitchUser:
        if force or channel not in self.user_data:
            self.user_data[channel] = await first(self.twitch_user.get_users(logins=[channel]))
        return self.user_data[channel]
    
    async def get_user_id(self, channel:str, force:bool=False) -> str:
        user = await self.get_user(channel, force)
        if user: return user.id

    async def get_stream_data(self, channel:str, force:bool=False) -> Stream:
        user_id = await self.get_user_id(channel, force)
        if user_id: return await first(self.twitch_user.get_streams(user_id=[user_id]))
    
    async def get_last_vod_data(self, channel:str, force:bool=False) -> Video:
        user_id = await self.get_user_id(channel, force)
        if user_id: return await first(self.twitch_user.get_videos(user_id=[user_id], video_type=VideoType.ARCHIVE))

    async def get_channel_data(self, channel:str, force:bool=False) -> ChannelInformation:
        user_id = await self.get_user_id(channel, force)
        if user_id: return (await self.twitch_user.get_channel_information(broadcaster_id=[user_id]))[0]

    async def get_shared_chat_session(self, channel:str, force:bool=False) -> SharedChatSession|None:
        user_id = await self.get_user_id(channel, force)
        if user_id: return await self.twitch_user.get_shared_chat_session(user_id)

    async def get_shared_chat_session_participants(self, session:SharedChatSession) -> list[TwitchUser]:
        if session is None: return []
        return await self.twitch_user.get_users(user_ids=[p.broadcaster_id for p in session.participants])

    async def get_shared_chat_participants(self, channel:str, force:bool=False) -> list[TwitchUser]:
        session = await self.get_shared_chat_session(channel, force)
        if session is None: return []
        return await self.get_shared_chat_session_participants(session)
 
    # -=-=- #
    
    async def get_random_clip_data(self, channel:str, force:bool=False) -> Clip|None:
        user_id = await self.get_user_id(channel, force)
        before = datetime.now() + timedelta(days=-90)
        clips = [clip async for clip in self.twitch_user.get_clips(broadcaster_id=user_id, is_featured=True, first=100)]
        if len(clips) > 0: return random.choice(clips)

    async def get_clip_data(self, url:str, clip:str=None, **_) -> Clip|None:
        clip_id = clip or url.split('?')[0].split('/')[-1]
        return await first(self.twitch_user.get_clips(clip_id=[clip_id]))

    # -=-=- #

    async def emit_status_change(self):
        status = {
            'live_viewers': self.viewers,
            'live_state':self.live_state if not self.shared_chat else LiveState.EXTRA,
            # -=-=- #
            'shared_chat': self.shared_chat,
            'shared_chat_host': self.shared_chat_host,
            'shared_chat_participants': self.shared_chat_participants,
            'shared_chat_viewers': self.shared_chat_viewers

        }
        await self.event_bus.emit(f"ChatStatusChangeEvent", ChatStatusChangeData(platform=Platform.TWITCH, status=status))

    @throttle(10)
    async def poll_shared_chat(self):
        session = await self.get_shared_chat_session(self.config.account_user)
        if session is None:
            self.shared_chat = False
            self.shared_chat_host = None
            self.shared_chat_participants = []
            self.shared_chat_viewers = 0
            return
        # -=-=- #
        participants = await self.get_shared_chat_session_participants(session)
        self.shared_chat = True
        self.shared_chat_host = session.host_display_name
        self.shared_chat_participants = [p.display_name for p in participants]
        self.shared_chat_viewers = sum(p.viewer_count for p in participants)

    @throttle(10)
    async def poll_data(self):
        stream = await self.get_stream_data(self.config.account_user)
        if stream is None:
            self.viewers = 0 # I think....
            await self.set_live_state(LiveState.OFFLINE)
            return 
        # -=-=- #
        self.viewers = stream.viewer_count
        await self.set_live_state(LiveState.ONLINE, False)
        # -=-=- #
        self.emit_status_change()

    # -=-=- #

    async def message_reply(self, message:str, data:ChatMessage|str):
        if isinstance(data, str):
            print(f"Cannot reply to message with id {data}")
            return
        # -=-=- #
        await data.reply(message)

    async def message_out(self, message:str, user_type:UserType=UserType.BOT, shared_chat:bool=False):
        """
        Send a chat message on Twitch.

        This method sends a message either as the streamer or the bot,
        and can optionally send it to shared chat if `shared_chat` is True.

        Parameters:
            msg (str): The message text to send.
            user_type (UserType): user type
            shared_chat (bool): If True, send the message to shared chat.
        """
        if not self.auth_done: return

        # if you want to force a message to be sent to shared chat
        if shared_chat:
            twitch_chat:chat.Chat = self.chat_user if user_type is UserType.USER else self.chat_bot
            await twitch_chat.send_message(self.config.account_user, message)
            return
        
        # get user ids
        channel_id = await self.get_user_id(self.config.account_user)
        user_id = channel_id if user_type is UserType.USER else await self.get_user_id(self.config.account_bot)

        # send the message
        await self.twitch_app.send_chat_message(channel_id, user_id, message, for_source_only=True)


    # -=-=- Events -=-=- #

    async def event_on_tick(self, _:OnTickData):
        await self.poll_data()

    async def query_get_twitch_viewers(self, _:QueryData) -> Response:
        await self.poll_shared_chat()
        await self.poll_data()
        return Response(self.viewers, viewers=self.viewers, shared_viewers=self.shared_chat_viewers)
    
    async def query_get_twitch_live_state(self, _:QueryData) -> Response:
        await self.poll_data()
        return Response(self.live_state, live_state=self.live_state)

    async def query_get_shared_chat_state(self, _:QueryData) -> Response:
        await self.poll_shared_chat()
        return Response(self.shared_chat, 
            shared_chat=self.shared_chat,
            shared_chat_host=self.shared_chat_host,
            shared_chat_participants=self.shared_chat_participants,
            shared_chat_viewers=self.shared_chat_viewers
        )

    # -=-=- #

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

    # -=-=- #

    async def event_on_ad_start(self, data:TwitchEventData[ChannelAdBreakBeginEvent]):
        # time = data.data.event.started_at
        # dur = data.data.event.duration_seconds
        await asyncio.sleep(data.data.event.duration_seconds)
        await self.event_bus.emit(f"TwitchAdStopEvent", data)

    # -=-=- #
    
    async def query_get_twitch_viewers(self, _:QueryData) -> Response:
        stream = await self.get_stream_data(self.config.account_user)
        viewers = stream is not None and stream.viewer_count or 0
        return Response(viewers, viewers=viewers)

    
    async def event_chat_message_out(self, data:"ChatMessageOutData"):
        if data.platform is not Platform.TWITCH: return
        # -=-=- #
        await self.message_out(data.message, data.user_type, data.shared_chat)

    # -=-=- #

    @queued
    async def event_shoutout_user(self, data:EventData):
        if not hasattr(data, 'user'): return
        # -=-=- #
        user:str = data.user.replace('@', '').strip().lower()
        user_id = await self.get_user_id(self.config.account_user)
        other_id = await self.get_user_id(user)
        # await self.out(f"Shouting out user: {user}")
        # -=-=- #
        for i in range(3):
            try: 
                await self.twitch_user.send_a_shoutout(user_id, other_id, user_id)
                break
            except TwitchAPIException as e:
                await self.out(f"Could not shout out user: {user}", MessageLevel.WARNING)
                return 
            except: # remove if doesn't work and just do manually
                await self.out(f"Retrying shout out (times: {i+1}): {user}", MessageLevel.WARNING)
                await asyncio.sleep(150)
            
        await self.out(f"Shouted out user: {user}")
        if self.event_shoutout_user.is_last() and not self.event_shoutout_user.is_only():
            await self.out(f"Evenrone shouted out!")
        
        # wait 2m10s before allowing another shoutout
        await self.event_shoutout_user.wait(user, timeout=130)


    async def event_start_raid(self, data:EventData):
        if not hasattr(data, 'user'): return
        # -=-=- #
        user:str = data.user.replace('@', '').strip().lower()
        user_id = await self.get_user_id(self.config.account_user)
        other_id = await self.get_user_id(user)
        await self.out(f"Raiding out user: {user}")
        # -=-=- #
        try: 
            await self.twitch_user.start_raid(user_id, other_id)
            await self.event_bus.emit('TwitchRaidStartedEvent', TwitchEventData(user, data=user))
        except TwitchAPIException as e:
            # await self.out(str(e))
            await self.out(f"Could not raid user: {user}", MessageLevel.ERROR)
            return
        
    async def event_stop_raid(self, _):
        user_id = await self.get_user_id(self.config.account_user)
        # -=-=- #
        await self.twitch_user.cancel_raid(user_id)

    # -=-=- #

    async def event_on_shared_chat_update(self, data:TwitchEventData[ChannelSharedChatUpdateEvent]):
        print(f"Shared Chat Updated: {data.data.event.participants}")
        
        participants = await self.get_shared_chat_session_participants(data.data.event)
        print(f"Shared Chat Members: {" ".join([p.display_name for p in participants])}")
        
        self.shared_chat = True
        self.shared_chat_host = data.data.event.host_broadcaster_user_name
        self.shared_chat_participants = [p.display_name for p in participants]
        self.shared_chat_viewers = sum(p.viewer_count for p in participants)

    async def event_on_shared_chat_begin(self, data:TwitchEventData[ChannelSharedChatBeginEvent]):
        print(f"Shared Chat Started - Host: {data.data.event.host_broadcaster_user_name}")
        
        participants = await self.get_shared_chat_session_participants(data.data.event)
        print(f"Shared Chat Members: {" ".join([p.display_name for p in participants])}")
 
        self.shared_chat = True
        self.shared_chat_host = data.data.event.host_broadcaster_user_name
        self.shared_chat_participants = [p.display_name for p in participants]
        self.shared_chat_viewers = sum(p.viewer_count for p in participants)
        

    async def event_on_shared_chat_end(self, data:TwitchEventData[ChannelSharedChatEndEvent]):
        print(f"Shared Chat Ended - Host: {data.data.event.host_broadcaster_user_name}")
        
        self.shared_chat = False
        self.shared_chat_host = None
        self.shared_chat_participants = []
        self.shared_chat_viewers = 0
        
    async def event_chat_notification(self, data:TwitchEventData[ChannelChatNotificationEvent]):
        print(f"Chat Notification ({data.data.event.notice_type}): {data.data.event.message.text}")
        print(f"Message Type: {data.data.metadata.message_type}")
        print(f"Chat Notification System Message: {data.data.event.system_message}")
        event = data.data.event
        if event.announcement is not None:
            print(f"Announcement: {event.announcement.to_dict()}")
        if event.charity_donation is not None:
            print(f"Charity Donation: {event.charity_donation.to_dict()}")

# EOF #
