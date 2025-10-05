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

from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from .settings import UserSettings


# -=-=- Functions and Classes -=-=- #

class UserEvents:
    def __init__(self, settings:"UserSettings"):
        self.settings = settings
        self.__register_events__()

    def __register_events__(self):
        raise NotImplementedError("UserEvents must implement __register_events__")


class DefaultEvents(UserEvents):
    def __init__(self, settings:"UserSettings"):
        super().__init__(settings)

    @override
    def __register_events__(self):
        print('Registering Default Events')