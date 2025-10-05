#! /usr/bin/env python3

"""
Single sentence description.

This package provides functionality for... [TODO - add description] 

Usage:
------
TODO
"""

# -=- EventBus Errors -=- #

class EventBusError(Exception):
    """Base class for all EventBus-related errors."""
    pass


class DuplicateEventIDError(EventBusError):
    """Raised when trying to register an event ID that already exists."""
    def __init__(self, event_id, event=None):
        msg = f"Event ID {event_id} is already registered"
        if event:
            msg += f" under event '{event}'"
        super().__init__(msg)


class EventNotFoundError(EventBusError):
    """Raised when trying to trigger or access a event that does not exist."""
    def __init__(self, event):
        super().__init__(f"Event ID '{event}' does not exist")


class EventIDNotFoundError(EventBusError):
    """Raised when trying to trigger or access a event that does not exist."""
    def __init__(self, event_id, event=None):
        msg = f"Event ID {event_id} does not exist"
        if event:
            msg += f" for event '{event}'"
        super().__init__(msg)


class ActionNotFoundError(EventBusError):
    """Raised when no action is associated with a given event ID."""
    def __init__(self, event_id, event=None):
        msg = f"No action found for event ID {event_id}"
        if event:
            msg += f" for event '{event}'"
        super().__init__(msg)


# -=- QueryBus Errors -=- #

class QueryBusError(Exception):
    """Base class for all QueryBus-related errors."""
    pass


class DuplicateQueryIDError(QueryBusError):
    """Raised when trying to register a query ID that already exists."""
    def __init__(self, query_id, query=None):
        msg = f"Query ID {query_id} is already registered"
        if query:
            msg += f" under query '{query}'"
        super().__init__(msg)


class QueryNotFoundError(QueryBusError):
    """Raised when trying to trigger or access a query that does not exist."""
    def __init__(self, query):
        super().__init__(f"Query ID '{query}' does not exist")


class QueryIDNotFoundError(QueryBusError):
    """Raised when trying to trigger or access a query that does not exist."""
    def __init__(self, query_id, query=None):
        msg = f"Query ID {query_id} does not exist"
        if query:
            msg += f" for query '{query}'"
        super().__init__(msg)


class HandlerNotFoundError(QueryBusError):
    """Raised when no handler is associated with a given query ID."""
    def __init__(self, query_id, query=None):
        msg = f"No handler found for query ID {query_id}"
        if query:
            msg += f" for query '{query}'"
        super().__init__(msg)
