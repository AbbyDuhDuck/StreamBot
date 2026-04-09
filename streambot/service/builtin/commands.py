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

from dataclasses import dataclass, field
import enum
from typing import Any, Callable

from .chat import ChatMessageData, ChatMessageOutData, ChatNotificationData, MessageLevel, Platform, UserType
from .sound import PlayTTSData
from .chat_twitch import SetGameData, TwitchChannelQueryData
from .chat_youtube import SetYouTubeIDData

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #

@configclass
class CommandsConfig(ConfigClass):
    admin_users:list[str] = field(default_factory=list)

# -=-=- Service Class -=-=- #

import asyncio


# -=-=- Function -=-=- #

def parse_command(message:str) -> tuple[str, str]:
    cmd = message.split()[0][1:].lower()
    args = " ".join(message.split()[1:])
    return cmd, args

# -=-=- Classes -=-=- #

class CommandLevel(enum.IntEnum):
    VIEWER = 0
    FOLLOWER = 1
    VIP = 2
    MOD = 3
    HEADMOD = 4
    ADMIN = 5

    @property
    def label(self) -> str:
        return {
            CommandLevel.VIEWER: "Viewer",
            CommandLevel.FOLLOWER: "Follower",
            CommandLevel.VIP: "VIP",
            CommandLevel.MOD: "Mod",
            CommandLevel.HEADMOD: "HeadMod",
            CommandLevel.ADMIN: "Admin",
        }[self]


@serviceclass("commands")
class CommandsService(BaseService[CommandsConfig]):
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
    
    async def message_out(self, message:str, user_type:UserType=UserType.BOT, platform:Platform=Platform.TWITCH):
        await EventBus.get_instance().emit("ChatMessageOut", ChatMessageOutData(message, user_type=user_type, platform=platform))

    async def display_out(self, message:str, level:MessageLevel=MessageLevel.INFO):
        await EventBus.get_instance().emit("ChatNotification", ChatNotificationData(message, level))

    # -=-=- #

    async def get_user_level(self, user:str) -> CommandLevel:
        broadcaster = (await QueryBus.get_instance().query("GetTwitchBroadcaster", QueryData)).get()
        head_mod = (await QueryBus.get_instance().query("GetTwitchHeadModerator", QueryData)).get()
        mods = (await QueryBus.get_instance().query("GetTwitchModerators", QueryData)).get()
        vips = (await QueryBus.get_instance().query("GetTwitchVIPs", QueryData)).get()
        is_follower = (await QueryBus.get_instance().query("IsTwitchFollower", TwitchChannelQueryData(channel=user))).get()

        # Normalize names
        user = user.lower()
        broadcaster = broadcaster.lower() if broadcaster else None
        admin_users = {u.lower() for u in self.config.admin_users}
        mod_users = {u.lower() for u in mods}
        vip_users = {u.lower() for u in vips}
        head_mod_user = head_mod.lower() if head_mod else None

        # Determine user's highest level
        if user in admin_users or user == broadcaster:
            user_level = CommandLevel.ADMIN
        elif user == head_mod_user:
            user_level = CommandLevel.HEADMOD
        elif user in mod_users:
            user_level = CommandLevel.MOD
        elif user in vip_users:
            user_level = CommandLevel.VIP
        elif is_follower:
            user_level = CommandLevel.FOLLOWER
        else:
            user_level = CommandLevel.VIEWER

        return user_level

    async def has_required_level(self, user:str, level:CommandLevel) -> bool:
        user_level = await self.get_user_level(user)
        print(f"User {user} has level {user_level.label} (required: {level.label})")
        return user_level >= level

    # -=-=- #

    def set_command(self, command:str, func:Callable[[str],Any], level:CommandLevel = CommandLevel.VIEWER):
        self.commands[command] = func
        self.command_levels[command] = level

    async def use_command(self, user:str, command:str, args:str):
        if command in self.commands:
            level = self.command_levels[command]
            # Check if the user has the required level to use the command
            if await self.has_required_level(user, level):
                await self.commands[command](user, args)
            else:
                print(f"User {user} does not have the required level to use command {command} (required: {level.label})")
            #     self.display_out(f"User {user} does not have the required level to use command {command}", MessageLevel.WARNING)
        # else:
        #     self.display_out(f"Command {command} not found!", MessageLevel.WARNING)

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
        user_level = await self.get_user_level(_user)
        commands_list = [cmd for cmd, lvl in self.command_levels.items() if lvl <= user_level]
        # commands_list = ", ".join(self.commands.keys())
        help_message = f"Available commands: {", ".join(commands_list)}"

        broadcaster = (await QueryBus.get_instance().query("GetTwitchBroadcaster", QueryData)).get()
        if _user.lower() != broadcaster: await self.message_out(help_message)
        await self.display_out(help_message)

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
