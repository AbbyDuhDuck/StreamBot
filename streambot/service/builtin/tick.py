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
import asyncio


# -=-=- Functions & Classes -=-=- #


# -=-=- Config Class -=-=- #

@configclass
class TickConfig(ConfigClass):
    tick_seconds:int = 1 # 1-second tick for the fast loop
    time_tick_seconds:int = 30 # 30-second tick for the slow loop

MULTIPLES_1 = [1, 3, 5, 10]
MULTIPLES_2 = [1, 2, 6, 10, 20]

# -=-=- Data Classes -=-=- #

@dataclass
class OnTickData(EventData):
    count:int

# -=-=- Service Class -=-=- #

@serviceclass("tick")
class AIService(BaseService[TickConfig]):
    """Emits tick events at different intervals/multiples."""
    event_bus:EventBus = EventBus.get_instance()

    def __init__(self, event_service):
        self.event_service = event_service
        self._tasks:list[asyncio.Task] = []

    async def start(self):
        # fast loop: 1,3,5,10 second ticks
        self._tasks.append(asyncio.create_task(self._second_tick_loop()))
        # slow loop: half-minute, 1m, 3m, 5m, 10m
        self._tasks.append(asyncio.create_task(self._time_tick_loop()))

    async def stop(self):
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    # ---------------- Fast tick loop ---------------- #
    async def _second_tick_loop(self):
        interval = 1
        count = 0
        while True:
            count += 1
            await asyncio.sleep(interval)
            # Emit events for specific multiples
            await self.event_bus.emit("OnOneSecondTick", OnTickData(count=count))
            if count % 3 == 0:
                await self.event_bus.emit("OnThreeSecondTick", OnTickData(count=count))
            if count % 5 == 0:
                await self.event_bus.emit("OnFiveSecondTick", OnTickData(count=count))
            if count % 10 == 0:
                await self.event_bus.emit("OnTenSecondTick", OnTickData(count=count))

    # ---------------- Time-based tick loop ---------------- #
    async def _time_tick_loop(self):
        interval = 30
        count = 0
        while True:
            count += 1
            await asyncio.sleep(interval)
            # Each tick represents 30 seconds
            await self.event_bus.emit("OnHalfMinuteTick", OnTickData(count=count * 0.5))
            if count % 2 == 0:  # 1 minute
                await self.event_bus.emit("OnOneMinuteTick", OnTickData(count=count * 0.5))
            if count % 6 == 0:  # 3 minutes
                await self.event_bus.emit("OnThreeMinuteTick", OnTickData(count=count * 0.5))
            if count % 10 == 0:  # 5 minutes
                await self.event_bus.emit("OnFiveMinuteTick", OnTickData(count=count * 0.5))
            if count % 20 == 0:  # 10 minutes
                await self.event_bus.emit("OnTenMinuteTick", OnTickData(count=count * 0.5))
    
    def __register_events__(self, event_bus):
        self.event_bus = event_bus

# EOF #
