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
from .commands import UserCommands, DefaultCommands
from .services import UserServices
import asyncio


# -=-=- Functions and Classes -=-=- #

class UserSettings:
    name:str
    account_user:str
    account_bot:str|None

    commands:UserCommands=DefaultCommands
    events:UserEvents=DefaultEvents
    services:UserServices

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

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        self.commands = self.commands(self)
        self.events = self.events(self)

        self.services.register_user_events()
        await self.services.start_all()



# EOF #
