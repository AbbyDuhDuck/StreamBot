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


# -=-=- Decorators -=-=- #

def track_args(cls):
    """
    Decorator that wraps the class __init__ to track which arguments were
    explicitly provided during instantiation.

    Positional and keyword arguments are recorded in `__provided_fields__`.
    """
    __init__ = cls.__init__

    @wraps(__init__)
    def init(self, *args, **kwargs):
        # make a set of field names that were given
        self.__provided_fields__ = set(kwargs.keys())
        # handle positional args
        for name, _ in zip([field.name for field in fields(cls)], args):
            self.__provided_fields__.add(name)
        # call the normal init
        __init__(self, *args, **kwargs)
    
    cls.__init__ = init
    return cls


def configclass(cls):
    """
    Decorator for dataclass-based configuration classes.

    Adds a `replace` method that allows replacing only the explicitly
    provided fields from another instance of the same class.
    """
    # Additionally decorates the class with @track_args and @dataclass
    # decorators.
    
    # inject replace method
    def _replace(self, config:Self) -> Self:
        """thing"""
        if not isinstance(config, type(self)):
            raise TypeError(f'Expected {type(self)} instance, got {type(config)} instead.')
        # -=-=- #
        fields = {field:getattr(config,field) for field in config.__provided_fields__}
        return replace(self, **fields)
    cls.replace = _replace
    # decorate class
    cls = dataclass(cls)
    cls = track_args(cls)
    return cls


# -=-=- Classes -=-=- #


class ConfigClass:
    """
    Base class for configuration objects.

    Intended to be used with the @configclass decorator. Provides type
    annotations for `replace` and `__provided_fields__`.
    """
    
    __provided_fields__: list[str]

    def replace(self, config:Self) -> Self:
        """Return a new instance with fields updated from `config`; raises TypeError if type mismatched."""
        ...


# EOF #
