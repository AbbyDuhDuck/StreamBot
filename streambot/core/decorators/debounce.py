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
import asyncio
from functools import wraps


def debounce(wait: float):
    """“only run after things stop happening”"""
    def decorator(func):
        task_name = f"_debounce_task_{func.__name__}"
        last_args_name = f"_debounce_args_{func.__name__}"

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # store latest call
            setattr(self, last_args_name, (args, kwargs))

            task: asyncio.Task = getattr(self, task_name, None)

            async def runner():
                try:
                    await asyncio.sleep(wait)
                    args_, kwargs_ = getattr(self, last_args_name)
                    await func(self, *args_, **kwargs_)
                except asyncio.CancelledError:
                    pass

            # cancel previous timer
            if task and not task.done():
                task.cancel()

            new_task = asyncio.create_task(runner())
            setattr(self, task_name, new_task)

        return wrapper
    return decorator


def throttle(wait: float):
    """run immediately, then block for a bit"""
    def decorator(func):
        lock_name = f"_throttle_lock_{func.__name__}"

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if getattr(self, lock_name, False):
                return

            setattr(self, lock_name, True)
            await func(self, *args, **kwargs)

            async def unlock():
                await asyncio.sleep(wait)
                setattr(self, lock_name, False)

            asyncio.create_task(unlock())

        return wrapper
    return decorator