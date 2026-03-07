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

from .events import UserEvents, DefaultEvents
from .services import UserServices

from ..signals import EventBus

import asyncio
from threading import Thread


# -=-=- Functions and Classes -=-=- #

class UserSettings:
    name:str
    account_user:str
    account_bot:str|None

    events:UserEvents=DefaultEvents
    services:UserServices

    stop_event:asyncio.Event = asyncio.Event()

    def __init__(
            self,
            name:str,
            account_user:str,
            account_bot:str|None=None,
    ):
        self.name = name
        self.account_user = account_user
        self.account_bot = account_bot

        self.services = UserServices(self)

        self.services.enable('sound')

        EventBus.get_instance().register('Stop', EventBus.lambda_action(lambda _: self.stop()))

    def stop(self):
        self.stop_event.set()

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        self.events = self.events(self)

        self.services.register_user_events()
        print("\nStarting Services...")
        await self.services.start_all()
        
        await self.wait_to_stop()
        
        print('\nStopping Services...')
        await self.services.stop_all()

    # -=-=- #

    async def wait_to_stop(self):
        self.wait_for_enter()
        await self.stop_event.wait()

    def wait_for_enter(self):
        # make a daemon thread and call stop if input happens
        def wait_for_input():
            input("\nPress Enter to Stop...\n\n")
            print("Enter Pressed, Stopping...")
            self.stop()
            
        thread = Thread(target=wait_for_input, daemon=True)
        thread.start()



# EOF #
