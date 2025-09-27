#! /usr/bin/env python3

"""
Provides the core functionality for the bot, ie. settings and startup.

This package provides a bunch of inheritable classes that can be used 
to provide functionality to the bot as well as settings that can be 
initialized to enable or configure different aspects or services that 
the bot provides. 

Modules & Subpackages:
----------------------
- TODO

Usage:
------
TODO
"""

# -=-=- Imports & Globals -=-=- #

from .usr.settings import UserSettings
from .usr.events import UserEvents
from .usr.commands import UserCommands

# EOF #
