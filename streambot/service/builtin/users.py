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

from dataclasses import dataclass, field
import enum
from typing import Any, Callable

from .chat import ChatMessageData, ChatMessageOutData, ChatNotificationData, MessageLevel, Platform, UserType

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

import random

from .chat_twitch import TwitchEventData
from .sound import PlayTTSData
from twitchAPI.object.eventsub import ChannelRaidEvent

from streambot.core.decorators import debounce

# -=-=- Functions & Classes -=-=- #

USER_DEBOUNCE_SECONDS = 15

# -=-=- Config Class -=-=- #

@configclass
class UsersConfig(ConfigClass):
    raid_cooldown:float = 60
    raid_minimum:int = 10

    # -=-=- #
    
    CALLOUTS:list[str] = field(default_factory=[
        "Welcome {user}",
        "Hello {user}",
        "Hello {user}",
        "Hi {user}",
        "Hi {user}",
        "Hey {user}",
        "Hey {user}",
        "{user}",
        "{user}",
    ].copy)
    GREETINGS:list[str] = field(default_factory=[
        "how are you?",
        "Welcome to the stream",
        "Welcome to the stream, I hope you have fun",
        "Welcome to the stream, I hope you have fun",
        "I hope you have fun today",
        "I hope you have fun tonight",
        "I hope you have fun tonight",
        "This is going to be a fun stream today",
        "This is going to be a fun stream tonight - I hope you enjoy it",
        "This is going to be a fun stream tonight - I hope you enjoy",
    ].copy)
    RETURNING_GREETINGS:list[str] = field(default_factory=[
        "Welcome back {user} - how are you?",
        "Hey {user} Welcome back - how are you?",
        "Hello {user} Welcome back - how are you?",
        "Welcome back {user}",
        "Welcome back {user}, I hope you have fun",
        "Hey {user} Welcome back , I hope you have fun today",
        "oh hey {user}, I hope you have fun tonight",
        "Welcome back {user}, This is going to be a fun stream today",
        "Welcome back {user}, This is going to be a fun stream today - I hope you enjoy it",
    ].copy)
    # -=-=- #
    LURK_MESSAGES:list[str] = field(default_factory=[
        '{user} flew away to watch from a distance.',
        'A wild {user} birb is lurking in the distance.',
        'On some branches is {user}, they perch with a flock of lurking birbs.',
        '{user} swims out on the pond to lurk with some ducks.',
    ].copy)

# -=-=- Data Classes -=-=- #

@dataclass
class UserData:
    user:str

@dataclass
class MessageData:
    message:str

# manage storing user data, user-specific commands, and user-specific events

# -=-=- Service Class -=-=- #

@serviceclass("users")
class UsersService(BaseService[UsersConfig]):
    nicknames:dict[str, str] = {}
    how_say:dict[str, str] = {}

    greetings:dict[str, list[str]] = {}
    lurk_messages:dict[str, list[str]] = {}

    _ignored_users = ["abbyduhduck", 'kofistreambot', 'nightbot', 'streamelements', 'blerp', 'artamisbot']

    greeting_queue:list[str] = []
    greeted_users:list[str] = []
    on_raid_cooldown:bool = False
    raiders:list[str] = []
    

    async def start(self):
        # print(f"Starting AI Service")
        pass

    async def stop(self):
        # print("Stopping AI Service")
        pass
    
    # -=-=- #

    async def say(self, message:str):
        await EventBus.get_instance().emit('PlayTTS', PlayTTSData(message))

    async def msg(self, message:str, user_type:UserType=UserType.BOT, platform:Platform=Platform.TWITCH):
        await EventBus.get_instance().emit("ChatMessageOut", ChatMessageOutData(message, user_type=user_type, platform=platform))

    async def out(self, message:str, level:MessageLevel=MessageLevel.INFO):
        await EventBus.get_instance().emit("ChatNotification", ChatNotificationData(message, level))

    # -=-=- #

    def __register_events__(self, event_bus):        
        event_bus.register("ChatMessage", self.event_chat_message)
        event_bus.register('OnGreetUser', self.event_greet_user)
        event_bus.register('OnTwitchRaidEvent', self.event_raid)
        
    def __register_queries__(self, query_bus):
        query_bus.register("GetUserGreeting", self.query_get_user_greeting)
        query_bus.register("GetUserNickname", self.query_get_user_nickname)

        query_bus.register("GetNickname", self.query_get_nickname)
        query_bus.register("GetLurkMessage", self.query_get_lurk_message)

    # -=-=- #

    def set_nickname(self, user:str, nickname:str|None=None, how_say:str|None=None):
        user = user.lower()
        if nickname: self.nicknames[user] = nickname
        if how_say: self.how_say[user] = how_say

    def get_matching(self, message:str) -> dict[str, dict[str, str|None]]:
        message = message.lower()
        matched:dict[str, dict[str, str|None]] = {}
        for user in set(self.nicknames) | set(self.how_say):
            nickname = self.nicknames.get(user)
            how_say = self.how_say.get(user)
            # -=-=- #
            data = {}
            if nickname: data['nickname'] = nickname
            if how_say: data['how_say'] = how_say
            # -=-=- #
            if user and user.lower() in message:
                matched[user] = data
            if nickname and nickname.lower() in message:
                matched[user] = data
        return matched
        
    # -=-=- #

    @debounce(USER_DEBOUNCE_SECONDS)
    async def greet_users(self):
        users = self.greeting_queue
        self.greeting_queue = []

        if self.can_greet(*users):
            users = self.get_valid_users(*users)
            print(f"Greeting: {self.get_names_string(*users)}")
            # -=-=- #
            await self.out(f"Greeting: {self.get_names_string(*users)}")
            for msg in self.get_greetings(*users):
                print(f'greeting: {msg}')
                await self.say(msg)
            self.greeted_users.extend(users)

    # -=-=- #

    def is_custom_user(self, user:str) -> bool:
        return user.lower() in self.greetings
    
    def is_returning_user(self, user:str) -> bool:
        return False

    
    def can_greet_user(self, user:str) -> bool:
        if user is None: return
        user = user.strip().lower()
        return True\
            and user != ''\
            and user not in self.greeted_users\
            and user not in self._ignored_users
    
    def can_greet(self, *users:str) -> bool:
        return bool(len(self.get_valid_users(*users)))

    def get_valid_users(self, *users:str):
        usrs = []
        for user in users:
            user = user.strip().lower()
            if user in usrs: continue
            if not self.can_greet_user(user): continue
            usrs.append(user)
        return usrs

    # -=-=- #
    
    def get_called_name(self, user:str) -> str:
        user = self.how_say.get('user', self.nicknames.get('user', user.lower()))
        return user.replace('_', ' ')
    
    def get_names_string(self, *users) -> str:
        users = [self.get_called_name(u) for u in users]
        if len(users) == 1:
            return users[0]
        return ', '.join(users[:-1]) + f', and {users[-1]}'
    
    # -=-=- #

    def get_greetings(self, *users:str) -> list[str]:
        users = self.get_valid_users(*users)
        custom_users = [u for u in users if self.is_custom_user(u)]
        returning_users = [u for u in users if u not in custom_users and self.is_returning_user(u)]
        new_users = [u for u in users if u not in [*custom_users, *returning_users]]
        greetings = []
        # -=-=- #
        if len(new_users):
            greetings.append(self._get_greeting(self.get_names_string(*new_users)))
        if len(returning_users):
            greetings.append(self._get_returning_greeting(self.get_names_string(*returning_users)))
        for user in custom_users:
            greetings.append(self._get_custom_greeting(user))
        # -=-=- #
        return greetings

    # -=-=- #

    def set_greetings(self, user:str, *greetings:str):
        user = user.lower()
        if user not in self.greetings: self.greetings[user] = []
        for greeting in greetings: self.greetings[user].append(greeting)

    def get_greeting(self, user:str) -> tuple[str, dict[str, dict]]:
        message = self._get_custom_greeting(user)
        matched = self.get_matching(message)
        return message, matched

    def set_lurk_messages(self, user:str, *lurk_messages:str):
        user = user.lower()
        if user not in self.lurk_messages: self.lurk_messages[user] = []
        for lurk_message in lurk_messages: self.lurk_messages[user].append(lurk_message)

    def get_lurk_message(self, user:str) -> tuple[str, dict]:
        message = self._get_custom_lurk_message(user)
        matched = self.get_matching(message)
        return message, matched

    # -=-=- #

    def _get_callout(self, user:str) -> str:
        return random.choice(self.config.CALLOUTS).format(user=user)
    
    def _get_greeting(self, user:str) -> str:
        return f"{self._get_callout(user)} - {random.choice(self.config.GREETINGS).format(user=user)}"

    def _get_returning_greeting(self, user:str) -> str:
        return random.choice(self.config.RETURNING_GREETINGS).format(user=user)

    def _get_custom_greeting(self, user:str) -> str:
        if user.lower() not in self.greetings: return self._get_greeting(user)
        return random.choice(self.greetings[user.lower()]).format(user=user)

    # -=-=- #

    def _get_lurk_message(self, user:str) -> str:
        return f"{self._get_callout(user)} - {random.choice(self.config.LURK_MESSAGES).format(user=user)}"
    
    def _get_custom_lurk_message(self, user:str) -> str:
        if user.lower() not in self.lurk_messages: return self._get_lurk_message(user)
        return random.choice(self.lurk_messages[user.lower()]).format(user=user)

    # TODO - add AI functionality here, such as responding to chat messages, generating text, etc.


    # -=-=- Events -=-=- #

    async def event_chat_message(self, data:ChatMessageData):
        if not self.can_greet_user(data.user): return
        if data.platform is not Platform.TWITCH: return
        if self.on_raid_cooldown and data.user.lower() not in self.raiders: return
        print(data.user)
        # -=-=- #
        self.greeting_queue.append(data.user)
        await self.greet_users()

    async def event_greet_user(self, data:UserData):
        greeting, nicknames = self.get_greeting(data.user)
        await self.say(greeting)

    async def event_raid(self, data:TwitchEventData[ChannelRaidEvent]):
        # TODO - add raided multiple time cuttoff too
        if data.data.event.viewers < self.config.raid_minimum: return
        # -=-=- #
        self.on_raid_cooldown = True
        user = data.data.event.from_broadcaster_user_login
        if user not in self.raiders: self.raiders.append(user)
        await asyncio.sleep(self.config.raid_cooldown)
        self.on_raid_cooldown = False

    # -=-=- #

    async def query_get_user_greeting(self, data:UserData) -> Response:
        greeting, nicknames = self.get_greeting(data.user)
        return Response(greeting, greeting=greeting, nicknames=nicknames)

    async def query_get_user_nickname(self, data:MessageData) -> Response:
        nicknames = self.get_matching(data.message)
        return Response(nicknames, nicknames=nicknames)

    async def query_get_nickname(self, data:UserData) -> Response:
        data = {}
        if data.user in self.nicknames: data['nickname'] = self.nicknames[data.user]
        if data.user in self.how_say: data['how_say'] = self.how_say[data.user]
        return Response(data, nicknames=data)

    async def query_get_lurk_message(self, data:UserData) -> Response:
        print(data)
        message, nicknames = self.get_lurk_message(data.user)
        return Response(message, message=message, micknames=nicknames)
    

# EOF #
