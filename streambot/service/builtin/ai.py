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

from dataclasses import dataclass
import enum
from typing import Any, Callable

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


# -=-=- Functions & Classes -=-=- #


# -=-=- Config Class -=-=- #

@configclass
class AIConfig(ConfigClass):
    pass

# -=-=- Service Class -=-=- #

import asyncio


# -=-=- Function -=-=- #



# -=-=- Classes -=-=- #

@serviceclass("ai")
class AIService(BaseService[ConfigClass]):

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
        # query_bus.register(
        #     'GetSoundService', 
        #     QueryBus.lambda_handler(lambda _: Response(self, service=self))
        # )
        pass

    # -=-=- #

    # TODO - add AI functionality here, such as responding to chat messages, generating text, etc.

    # -=-=- Events -=-=- #

    # TODO - add event handlers here, such as for chat messages, commands, etc.


# TODO - dataclasses for event data, query data, etc. related to AI functionality.

# EOF #
