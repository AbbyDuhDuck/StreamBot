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
from typing import override, TYPE_CHECKING
from dataclasses import dataclass, fields, replace, field
from typing import TypeVar, Self, Any, Type, Callable, Generic
from functools import wraps
import asyncio

if TYPE_CHECKING:
    from .base import BaseService

# -=-=- Registry -=-=- #


SERVICE_REGISTRY: dict[str, type["BaseService"]] = {}

def register(name: str):
    def _decorator(cls):
        SERVICE_REGISTRY[name] = cls
        return cls
    return _decorator

def get_service(name: str):
    return SERVICE_REGISTRY.get(name)

# EOF #
