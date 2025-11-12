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

from .exceptions import DuplicateEventIDError, ActionNotFoundError, EventNotFoundError, EventIDNotFoundError


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

    # -=-=- Helpers -=-=- #

    @staticmethod
    def lambda_action(action:Coroutine) -> Coroutine:
        async def func(event:EventData):
            action(event)
        return func
    
    
    # -=-=- Register and Unregister -=-=- #

    def register(self, event:str, action:Coroutine) -> UUID:
        """register a action to an event"""
        id = uuid4()
        self.add_event_id(id, event)
        self.set_action(id, action)
        return id

    def unregister(self, id:UUID):
        """unregister an event"""
        self.remove_event_id(id)
        self.remove_action(id)

    # -=-=- Trigger -=-=- #

    async def emit(self, event:str, data:EventData=object(), wait: bool = True, sequential: bool = False):
        """
        Trigger an event with optional blocking and sequential execution.

        Parameters
        ----------
        event : str
            The event to trigger.
        data : EventData, optional
            Data to pass to the handlers. Defaults to empty object.
        wait : bool, optional
            Should this emit call block program flow until handlers finish? Defaults to True.
        sequential : bool, optional
            Should handlers run one at a time? Defaults to False (all concurrently).
        """
        # -=- Waiting & Non-Sequential -=- #
        if wait and not sequential:
            [
                print(f"Handler error: {result}")
                for result in await asyncio.gather(
                    *(action(data) for action in self.get_event_actions(event)),
                    return_exceptions=True
                )
                if isinstance(result, Exception)
            ]
        # -=- Waiting & Sequential -=- #
        elif wait and sequential:
            for action in self.get_event_actions(event):
                try: await action(data)
                except Exception as e:
                    print(f"Handler error: {e}")
        # -=- Non-Waiting & Non-Sequential -=- #
        elif not wait and not sequential:
            [
                asyncio.create_task(action(data)).add_done_callback(lambda task: 
                    print(f"Handler error: {task.exception()}") 
                    if task.exception() else None
                ) 
                for action in self.get_event_actions(event)
            ]
        # -=- Non-Waiting & Sequential -=- #
        else:
            asyncio.create_task(self.emit(event, data, wait=True, sequential=True))
            
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
        # maybe raise not found error?
        return self.registered[event] if self.event_exists(event) else []
    
    def get_event_actions(self, event:str) -> list[Coroutine]:
        """get the event actions by name"""
        return [self.get_action(id) for id in self.get_event_ids(event)]
    
    def get_action(self, id:UUID) -> Coroutine:
        """get the event action by its id"""
        if not self.action_exists(id):
            raise ActionNotFoundError(id, self.get_event_name(id))
        return self.actions[id]

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
            self.registered[event].remove(id)
        if len(self.registered[event]) == 0:
            del self.registered[event]


    # -=-=- #

    def set_action(self, id:UUID, action:Coroutine):
        """set the action for a defined event id"""
        self.actions[id] = action

    def remove_action(self, id:UUID):
        """remove the action from a defined event id"""
        if not self.action_exists(id): return
        del self.actions[id]


    



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

    # decorated handler to test the async blocking
    def wait_time(seconds:float):
        async def func(_: BitsEvent):
            await asyncio.sleep(seconds)
            print(f"waited {seconds} seconds")
        return func
    
    # handler
    async def bits_handler(event: BitsEvent):
        print(f"{event.user} donated {event.amount} bits!")

    async def main():
        bus = EventBus.get_instance()

        # Register the handler
        event_id = bus.register("bits_donated", wait_time(5))
        event_id = bus.register("bits_donated", wait_time(2))
        event_id = bus.register("bits_donated", wait_time(1))
        event_id = bus.register("bits_donated", bits_handler)

        print('# -=- Running Tests -=- #\n')

        # Emit the event
        print("Testing with non-waiting and non-sequential")
        await bus.emit("bits_donated", BitsEventData(user="NonBlocking", amount=500), wait=False, sequential=False)
        
        print("Testing with waiting and non-sequential")
        await bus.emit("bits_donated", BitsEventData(user="GenericUser", amount=500), wait=True, sequential=False)
        
        await asyncio.sleep(1)
        print('\n# -=-=- #\n')

        print("Testing with non-waiting and sequential")
        await bus.emit("bits_donated", BitsEventData(user="GenericUser", amount=500), wait=False, sequential=True)

        print("Testing with waiting and sequential")
        await bus.emit("bits_donated", BitsEventData(user="GenericUser", amount=500), wait=True, sequential=True)

        await asyncio.sleep(1)
        print('\n# -=-=- #\n')

        print("Testing with defualt parameters")
        await bus.emit("bits_donated", BitsEventData(user="GenericUser", amount=500))

        # Cleanup
        bus.unregister(event_id)

    asyncio.run(main())


# EOF #
