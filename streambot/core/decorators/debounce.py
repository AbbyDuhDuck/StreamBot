#! /usr/bin/env python3

# give the bot AI capabilities. 

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

import asyncio
from functools import wraps
from typing import Any, Callable

# -=-=- #

def debounce(wait: float):
    """
    Debounce decorator for async functions.
    Only calls the function after `wait` seconds have passed since the last call.
    Any calls during the wait period cancel the previous scheduled call.
    """
    def decorator(func):
        task_name = f"_debounce_task_{func.__name__}"

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Cancel any existing task
            task:asyncio.Task = getattr(self, task_name, None)
            if task and not task.done():
                task.cancel()

            # Schedule new task
            async def call_later():
                try:
                    await asyncio.sleep(wait)
                    await func(self, *args, **kwargs)
                except asyncio.CancelledError:
                    pass  # Ignore if cancelled by a new call

            new_task = asyncio.create_task(call_later())
            setattr(self, task_name, new_task)

        return wrapper
    return decorator