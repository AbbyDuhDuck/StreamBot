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


# -=-=- Functions and Classes -=-=- #

class UserSettings:
    name:str
    account_user:str
    account_bot:str|None

    commands:UserCommands=DefaultCommands
    events:UserEvents=DefaultEvents

    def __init__(
            self,
            name:str,
            account_user:str,
            account_bot:str|None=None,
    ):
        self.name = name
        self.account_user = account_user
        self.account_bot = account_bot

    def run(self):
        self.commands = self.commands(self)
        self.events = self.events(self)
        # TODO start user services


# EOF #
