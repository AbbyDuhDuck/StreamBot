#! /usr/bin/env python3

"""User Setup"""

# -=-=- Imports & Globals -=-=- #

from src.bot import UserSettings

# from .commands import CustomCommands
# from .events import CustomEvents

# -=-=- #

SETTINGS = UserSettings(
    name="ExampleBot",
    account_user="ExampleUser",
    # account_bot="ExampleBot",
)

# SETTINGS.events = CustomEvents

