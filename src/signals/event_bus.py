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

from typing import Coroutine, Protocol
from uuid import uuid4, UUID

from .exceptions import DuplicateEventIDError, ActionNotFoundError


# -=-=- Functions and Classes -=-=- #


class EventData(Protocol):
    """Data from a triggered event."""
    pass



class EventBus:
    """
    Manages registering events and services as well as triggering and
    handling them when called.
    """
    _instance_:"EventBus" = None

    registered:dict[str, list[UUID]] = {}
    actions: dict[UUID, Coroutine] = {}

    @staticmethod
    def get_instance() -> "EventBus":
        if EventBus._instance_ is None:
            EventBus._instance_ = EventBus()
        return EventBus._instance_

    # -=-=- Register and Unregister -=-=- #

    def register(self, event:str, callback:Coroutine) -> UUID:
        """register a callback to an event"""

    def unregister(self, id:UUID):
        """unregister an event"""

    # -=-=- Trigger -=-=- #

    async def emit(self, event:str, data:EventData):
        """trigger an event"""

    # -=-=- Exists -=-=- #

    def event_exists(self, event:str) -> bool:
        """checks if an event exists"""
        return event in self.registered

    def event_id_exists(self, id:UUID, event:str|None=None) -> bool:
        """checks if an event id exists in an event"""
        if event is not None:
            return id in self.registered[event]
        return self.get_event_name(id) is not None

    def action_exists(self, id:UUID) -> bool:
        """checks if an action exists for a given id"""
        return id in self.actions

    # -=-=- Getters and Setters -=-=- #

    def get_event_name(self, id:UUID) -> str:
        """get an event name from an ID it contains"""
        for event in self.registered:
            if id in self.registered[event]:
                return event


    def get_event_ids(self, event:str) -> list[UUID]:
        """get the event ids by name"""
        return self.registered[event] if self.event_exists(event) else []

    def add_event_id(self, id:UUID, event:str):
        """add an event id to the currently usable ones for that name"""
        if self.event_id_exists(id):
            raise DuplicateEventIDError(id, self.get_event_name(id))
        if not self.event_exists(event): self.registered[event] = []
        self.registered[event].append(id)

    def remove_event_id(self, id:UUID, event:str|None=None):
        """remove the id from the active events"""
        if event is None: event = self.get_event_name(id)
        if self.event_id_exists(id, event):
            del self.registered[event][id]

    # -=-=- #

    def set_action(self, id:UUID, callback:Coroutine):
        """set the action for a defined event id"""
        self.actions[id] = callback

    def remove_action(self, id:UUID):
        """remove the action from a defined event id"""
        if not self.action_exists(id): return
        del self.actions[id]

    # -=-=- #



# -=-=- Main -=-=- #

if __name__ == "__main__":
    import asyncio
    from dataclasses import dataclass
    from uuid import UUID

    # Define a simple BitsEvent
    @dataclass
    class BitsEventData:
        user: str
        amount: int

    # Optional: subclass if you use EventData base
    class BitsEvent(EventData):
        user: str
        amount: int

    async def bits_handler(event: BitsEvent):
        print(f"{event.user} donated {event.amount} bits!")

    async def main():
        bus = EventBus.get_instance()

        # Register the handler
        event_id = bus.register("bits_donated", bits_handler)

        # Emit the event
        await bus.emit("bits_donated", BitsEventData(user="GenericUser", amount=500))

        # Cleanup
        bus.unregister(event_id)

    asyncio.run(main())


# EOF #
