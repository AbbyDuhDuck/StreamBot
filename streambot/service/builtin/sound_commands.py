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
from datetime import datetime, timedelta
import enum
import random
import re
from typing import Any, Callable


from .sound import AddSFXData, PlaySFXData
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
    sound_groups:dict[str, list[str]] = {}
    sound_triggers:dict[str, str] = {}
    user_triggers:dict[str, str] = {}
    cooldowns:dict[str, float] = {}
    cooldown_times:dict[str, datetime] = {}

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
        event_bus.register("SetSoundGroup", self.event_set_sound_group)
        event_bus.register("SetSoundTrigger", self.event_set_sound_trigger)
        
    def __register_queries__(self, query_bus):
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )
        pass

    # -=-=- #

    async def set_sound(self, name:str, filepath:str, volume:float = 1.0, cooldown:float = 0):
        """Set a sound command - e.g. bonk -> bonk.wav"""
        await EventBus.get_instance().emit("AddSFX", AddSFXData(name=name, filepath=filepath, volume=volume))
        self.set_cooldown(name, cooldown)

    def set_sound_group(self, name:str, *sounds:list[str], cooldown:float = 0):
        """Set a sound group - e.g. quack -> [quack1, quack2, quack3]"""
        self.sound_groups[name] = sounds
        self.set_cooldown(name, cooldown)

    def set_trigger(self, name:str, regex:str):
        """Set a sound trigger - e.g. wee <- /wee+?/"""
        self.sound_triggers[name] = regex

    def set_user_trigger(self, user:str, sound:str):
        """Set a sound trigger for when a user chats - e.g. quack.wav when MrsDuck chats"""
        self.user_triggers[user] = sound
    
    def set_cooldown(self, name:str, cooldown:float):
        """Set a cooldown for a sound command or group - e.g. bonk has a 10 second cooldown"""
        self.cooldowns[name] = cooldown
        self.cooldown_times[name] = datetime.now()

    # -=-=- #

    def is_on_cooldown(self, name:str) -> bool:
        if name in self.cooldowns:
            seconds = self.cooldowns[name]
            time = datetime.now() - timedelta(seconds=seconds)
            if time < self.cooldown_times[name]:
                return True
        return False
    
    def is_trigger_match(self, regex:str, message:str) -> str|None:
        return re.search(regex, message.lower()) is not None
    
    async def get_trigger_match(self, message:str) -> str|None:
        for name, regex in self.sound_triggers.items():
            if self.is_trigger_match(regex, message):
                return name
        return None
    
    async def try_sound_command(self, message:str, user:str):
        if user in self.user_triggers:
            return await self.try_play_sound(self.user_triggers[user])
        # -=-=- #
        name = await self.get_trigger_match(message)
        if name is None: return
        # -=-=- #
        if name in self.sound_groups:
            return await self.try_play_sound_group(name)
        await self.try_play_sound(name)
    
    async def try_play_sound_group(self, name:str):
        if name not in self.sound_groups: return
        if self.is_on_cooldown(name): return
        # -=-=- #
        sound = random.choice(self.sound_groups[name])
        await EventBus.get_instance().emit("PlaySFX", PlaySFXData(name=sound))
        self.cooldown_times[name] = datetime.now()

    async def try_play_sound(self, name:str):
        if self.is_on_cooldown(name): return
        # -=-=- #
        await EventBus.get_instance().emit("PlaySFX", PlaySFXData(name=name))
        self.cooldown_times[name] = datetime.now()

    # -=-=- Events -=-=- #

    async def event_chat_message_in(self, data:"ChatMessageData"):
        print(f'Chat Message In from {data.user}: {data.message}')
        # -=-=- #
        await self.try_sound_command(data.message, data.user)
        

    async def event_set_sound_command(self, data:"SetSoundCommandData"):
        await self.set_sound(data.sound, data.filepath, data.volume, data.cooldown)
        if data.trigger is not None:
            self.set_trigger(data.sound, data.trigger)

    async def event_set_sound_group(self, data:"SetSoundGroupData"):
        self.set_sound_group(data.group, data.sounds, data.cooldown)
        if data.trigger is not None:
            self.set_trigger(data.group, data.trigger)

    async def event_set_sound_trigger(self, data:"SetSoundTriggerData"):
        self.set_trigger(data.sound, data.trigger)


@dataclass
class SetSoundCommandData(EventData):
    sound:str
    filepath:str
    volume:float = 1.0
    cooldown:float|None = None
    trigger:str|None = None

@dataclass
class SetSoundGroupData(EventData):
    group:str
    sounds:list[str]
    cooldown:float|None = None
    trigger:str|None = None

@dataclass
class SetSoundTriggerData(EventData):
    sound:str
    trigger:str

# EOF #
