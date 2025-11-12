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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from .settings import UserSettings


# -=-=- Functions and Classes -=-=- #

class UserEvents(ABC):
    def __init__(self, settings:"UserSettings"):
        self.settings = settings
        self.register_events()

    @abstractmethod
    def register_events(self): ...

class DefaultEvents(UserEvents):
    def __init__(self, settings:"UserSettings"):
        super().__init__(settings)

    def register_events(self):
        print('Registering Default Events')