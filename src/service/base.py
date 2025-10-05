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
from typing import override
from dataclasses import dataclass, fields, replace, field
from typing import TypeVar, Self, Any, Type, Callable, Generic
from functools import wraps
import asyncio

from .config import ConfigClass
from .registry import register


# -=-=- Functions & Classes -=-=- #


def serviceclass(arg=None, *, name:str|None=None):
    """
    Decorator for defining a service class. 
    If `name` is provided, the service is automatically registered.
    
    Can be used as:
      @serviceclass
      class MyService: ...

    or:
      @serviceclass()
      class MyService: ...

    or:
      @serviceclass("name")
      class MyService: ...

    or:
      @serviceclass(name="name")
      class MyService: ...

    """
    # correct for positional arg passed like @serviceclass("name")
    if isinstance(arg, str):
        name = arg
        arg = None
    # -=-=- #
    def wrap(cls):
        # add the Config type for its definition
        config_type = getattr(cls, "__orig_bases__", [None])[0].__args__[0]
        cls.Config = config_type
        # register the class if name is provided 
        if name: register(name)(cls)
        # -=-=- #
        return cls
    # Allow decorator to be used with or without parentheses
    if arg is None:
        return wrap
    else:
        return wrap(arg)


C = TypeVar("C", bound=ConfigClass)

class BaseService(ABC, Generic[C]):
    """Abstract Service Base Class for internal and user defined services to build upon"""

    Config:C

    def __init__(self, config:C|None = None):
        self.config:C = config or self.Config()

    def configure(self, config:C):
        """Update the service's config."""
        self.config = self.config.replace(config)
    
    @abstractmethod
    async def start(self): ...

    @abstractmethod
    async def stop(self): ...


# EOF #
