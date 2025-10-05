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

from typing import TYPE_CHECKING

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
