#! /usr/bin/env python3

# sound commands - sound fx

# Simple to implement, 

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

from .chat import ChatMessageData

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


ADMIN_USERS = ["abbyduhduck"]

# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #


# -=-=- Service Class -=-=- #

import asyncio


# -=-=- Function -=-=- #



# -=-=- Classes -=-=- #


@serviceclass("sound_commands")
class SoundCommandsService(BaseService[ConfigClass]):

    async def start(self):
        # print(f"Starting Commands Service")
        pass

    async def stop(self):
        # print("Stopping Commands Service")
        pass
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register("ChatMessageIn", self.event_chat_message_in)
        event_bus.register("SetSoundCommand", self.event_set_sound_command)
        event_bus.register("SetSoundTrigger", self.event_set_sound_trigger)
        
    def __register_queries__(self, query_bus):
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )
        pass

    # -=-=- #

    def set_command(self, ):
        """Set a sound command - e.g. bonk -> bonk.wav"""
        pass

    def set_trigger(self, ):
        """Set a sound trigger - e.g. wee <- /wee+?/"""
        pass

    def set_user_trigger(self, ):
        """Set a sound trigger for when a user chats - e.g. quack.wav when MrsDuck chats"""
        pass

    # -=-=- Events -=-=- #

    async def event_chat_message_in(self, data:"ChatMessageData"):
        print(f'Chat Message In from {data.user}: {data.message}')
        # -=-=- #
        pass

    async def event_set_sound_command(self, data:"SetSoundCommandData"):
        pass

    async def event_set_sound_trigger(self, data:"SetSoundTriggerData"):
        pass


# TODO - add dataclasses here 
@dataclass
class SetSoundCommandData(EventData):
    command:str

@dataclass
class SetSoundTriggerData(EventData):
    command:str

# EOF #
