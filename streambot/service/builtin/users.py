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

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

import random

# -=-=- Functions & Classes -=-=- #


# -=-=- Config Class -=-=- #

@configclass
class UsersConfig(ConfigClass):
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

# TODO - dataclasses for event data, query data, etc. related to AI functionality.

# manage storing user data, user-specific commands, and user-specific events

# -=-=- Service Class -=-=- #

@serviceclass("users")
class UsersService(BaseService[UsersConfig]):
    nicknames:dict[str, str] = {}
    how_say:dict[str, str] = {}

    greetings:dict[str, list[str]] = {}
    lurk_messages:dict[str, list[str]] = {}

    _ignored_users = ["abbyduhduck", 'KofiStreamBot', 'nightbot', 'StreamElements', 'blerp']

    async def start(self):
        # print(f"Starting AI Service")
        pass

    async def stop(self):
        # print("Stopping AI Service")
        pass
    
    # -=-=- #

    def __register_events__(self, event_bus):
        # event_bus.register("ChatMessageIn", self.event_chat_message_in)
        pass
        
    def __register_queries__(self, query_bus):
        query_bus.register("GetUserGreeting", self.query_get_user_greeting)
        query_bus.register("GetUserNickname", self.query_get_user_nickname)

        query_bus.register("GetNickname", self.query_get_nickname)
        query_bus.register("GetLurkMessage", self.query_get_nickname)

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

    def get_lurk_message(self, user:str) -> str:
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

    async def query_get_user_greeting(self, data) -> Response:
        greeting, nicknames = self.get_greeting(data.user)
        return Response(greeting, greeting=greeting, nicknames=nicknames)

    async def query_get_user_nickname(self, data) -> Response:
        nicknames = self.get_matching(data.message)
        return Response(nicknames, nicknames=nicknames)

    async def query_get_nickname(self, data) -> Response:
        data = {}
        if data.user in self.nicknames: data['nickname'] = self.nicknames[data.user]
        if data.user in self.how_say: data['how_say'] = self.how_say[data.user]
        return Response(data, nicknames=data)

    async def query_get_lurk_message(self, data) -> Response:
        message = self.get_lurk_message(data.user)
        return Response(message, message=message)


# EOF #
