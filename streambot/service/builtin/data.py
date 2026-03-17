#! /usr/bin/env python3

# managing storing general stream data and global values

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
import asyncio


# -=-=- Functions & Classes -=-=- #



# -=-=- Config Class -=-=- #

@configclass
class DataConfig(ConfigClass):
    pass

# -=-=- Data Classes -=-=- #

# TODO - dataclasses for event data, query data, etc. related to AI functionality.


# -=-=- Service Class -=-=- #

@serviceclass("data")
class DataService(BaseService[DataConfig]):

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

    # TODO - add functionality here

    # -=-=- Events -=-=- #

    # TODO - add event handlers here


# EOF #
