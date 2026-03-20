#! /usr/bin/env python3

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

from dataclasses import dataclass
import enum
from typing import Any, Callable

from .chat import ChatMessageData, ChatMessageOutData
from .sound import PlayTTSData
from .chat_twitch import SetGameData
from .chat_youtube import SetYouTubeIDData
from .webui.webui import DisplayOutData

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


ADMIN_USERS = ["abbyduhduck"]

# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #


# -=-=- Service Class -=-=- #

import asyncio


# -=-=- Function -=-=- #

def parse_command(message:str) -> tuple[str, str]:
    cmd = message.split()[0][1:].lower()
    args = " ".join(message.split()[1:])
    return cmd, args

# -=-=- Classes -=-=- #

class CommandLevel(enum.Enum):
    VIEWER = "Viewer"
    FOLLOWER = "Follower"
    VIP = "VIP"
    MOD = "Mod"
    HEADMOD = "HeadMod"
    ADMIN = "Admin"


@serviceclass("commands")
class CommandsService(BaseService[ConfigClass]):
    commands:dict[str, Callable[[str],Any]] = {}
    command_levels:dict[str, CommandLevel] = {}

    async def start(self):
        # print(f"Starting Commands Service")
        pass

    async def stop(self):
        # print("Stopping Commands Service")
        pass
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register("ChatMessage", self.event_chat_message)
        event_bus.register("ChatCommand", self.event_chat_command)
        
    def __register_queries__(self, query_bus):
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )
        pass

    # -=-=- #

    def has_required_level(self, user:str, level:CommandLevel) -> bool:
        # Placeholder implementation - replace with actual user level checking logic
        if level == CommandLevel.VIEWER:
            return True
        elif level == CommandLevel.FOLLOWER:
            return user.lower() in ADMIN_USERS
            return False # TODO: Implement follower check
        elif level == CommandLevel.VIP:
            return user.lower() in ADMIN_USERS
            return False # TODO: Implement VIP check
        elif level == CommandLevel.MOD:
            return user.lower() in ADMIN_USERS
            return False # TODO: Implement mod check
        elif level == CommandLevel.HEADMOD:
            return user.lower() in ADMIN_USERS
            return False # TODO: Implement head mod check
        elif level == CommandLevel.ADMIN:
            return user.lower() in ADMIN_USERS

    # -=-=- #

    def set_command(self, command:str, func:Callable[[str],Any], level:CommandLevel = CommandLevel.VIEWER):
        self.commands[command] = func
        self.command_levels[command] = level

    async def use_command(self, user:str, command:str, args:str):
        if command in self.commands:
            level = self.command_levels[command]
            # Check if the user has the required level to use the command
            if self.has_required_level(user, level):
                await self.commands[command](user, args)
            else:
                print(f"User {user} does not have the required level to use command {command}")
        else:
            print(f"Command {command} not found!")

    # -=-=- #

    def add_default_commands(self):
        self.set_command('commands', self.command_help, CommandLevel.VIEWER)
        self.set_command('help', self.command_help, CommandLevel.VIEWER)
        
        self.set_command('tts', self.command_tts, CommandLevel.MOD)
        
        self.set_command('game', self.command_game, CommandLevel.MOD)
        self.set_command('youtube_id', self.command_youtube_id, CommandLevel.MOD)
    
        self.set_command('!', self.command_tts, CommandLevel.ADMIN)
        self.set_command('stop', self.command_stop, CommandLevel.ADMIN)

    # -=-=- Commands -=-=- #

    async def command_help(self, _user:str, _args:str):
        commands_list = ", ".join(self.commands.keys())
        help_message = f"Available commands: {commands_list}"
        
        await EventBus.get_instance().emit("DisplayOut", DisplayOutData(message=help_message))
        await EventBus.get_instance().emit("MessageOut", ChatMessageOutData(message=help_message))

    async def command_tts(self, user:str, args:str):
        await EventBus.get_instance().emit("PlayTTS", PlayTTSData(message=args))

    async def command_game(self, user:str, args:str):
        await EventBus.get_instance().emit("SetGame", SetGameData(game=args))

    async def command_youtube_id(self, user:str, args:str):
        await EventBus.get_instance().emit("SetYouTubeID", SetYouTubeIDData(youtube_id=args))

    async def command_stop(self, user:str, args:str):
        await EventBus.get_instance().emit("Stop")

    # -=-=- Events -=-=- #

    async def event_chat_message(self, data:"ChatMessageData"):
        if not data.message.startswith("!"): return
        # -=-=- #
        cmd, args = parse_command(data.message)
        await EventBus.get_instance().emit("ChatCommand", ChatCommandData(command=cmd, args=args, user=data.user))

    async def event_chat_command(self, data:"ChatCommandData"):
        # print(f'Chat Command In from {data.user}: {data.command} {data.args}')
        await self.use_command(data.user, data.command, data.args)


@dataclass
class ChatCommandData(EventData):
    command:str
    args:str
    user:str

# EOF #
