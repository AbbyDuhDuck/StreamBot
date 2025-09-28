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

from typing import Coroutine, Any
from uuid import uuid4, UUID


# -=-=- Functions and Classes -=-=- #


class EventData:
    """Data from a triggered event."""
    pass


class Response:
    """Response from a triggered service."""
    pass


# class Event:
#     """
#     An Event Object that can be triggered or subscribed to.
    
#     To be triggered to cause an effect and not return data. Multiple
#     objects can subscribe a method to this Event to be called when it
#     gets triggered.
#     """
#     pass


# class Service:
#     """
#     A Service Object that can be called to get data from the object
#     that registered it. 
    
#     Should only retrieve data from an object not create an effect when
#     called. Services that cause an effect should be marked as such with
#     the variable `TODO` set to true. 
#     """
#     pass


class EventManager:
    """
    Manages registering events and services as well as triggering and
    handling them when called.
    """
    
    def __init__(self):
        """singleton + docstring"""
        pass

    def init(self):
        """initialize the event manager"""
        pass

    # -=-=- Register and Unregister -=-=- #

    def register_event(self, name:str, callback:Coroutine) -> UUID:
        """register a callback to an event"""
    
    def register_service(self, name:str, callback:Coroutine) -> UUID:
        """register a callback to a service"""

    def unregister_event(self, id:UUID):
        """unregister an event (maybe not needed)"""
    
    def unregister_service(self, id:UUID):
        """unregister a service (maybe not needed)"""

    def unregister(self, id:UUID):
        """unregister an event or service"""

    # -=-=- Trigger -=-=- #

    def trigger_event(self, name:str, data:dict[str, Any]):
        """trigger an event"""

    def trigger_service(self, name:str, data:dict[str, Any]) -> Response:
        """trigger a service"""

    # -=-=- Exists -=-=- #

    def is_event(self, name:str) -> bool:
        """checks if an event exists"""

    def is_service(self, name:str) -> bool:
        """checks if a service exists"""

    def is_event_id(self, id:UUID) -> bool:
        """checks if an event id exists"""

    def is_service_id(self, id:UUID) -> bool:
        """checks if a service id exists"""

    # -=-=- Getters and Setters -=-=- #

    def get_events(self, name:str) -> list[UUID]:
        """get the event ids by name"""

    def get_service(self, name:str) -> UUID:
        """get the service id by name"""

    def add_event(self, name:str, id:UUID):
        """add an event id to the currently usable ones for that name"""

    def set_service(self, name:str, id:UUID):
        """set a service id to the current name"""

    def remove_event(self, id:UUID):
        """remove the id from the active events"""

    def remove_service(self, id:UUID):
        """remove the id from the active services"""

    def set_action(self, id:UUID, callback:Coroutine):
        """set the action for a defined id (service or event)"""

    def remove_action(self, id:UUID):
        """remove the action from a defined id (service or event)"""

    # -=-=- #

