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

from typing import Coroutine, Protocol
from uuid import uuid4, UUID

from .exceptions import DuplicateQueryIDError, QueryNotFoundError, HandlerNotFoundError


# -=-=- Functions and Classes -=-=- #


class QueryData(Protocol):
    """Data from a triggered query."""
    pass


class Response:
    """Flexible response object for QueryBus."""

    def __init__(self, *args, **kwargs):
        RESERVED_NAMES = {"__value__", "__data__", "get", "all"}
        
        # Handle positional arguments
        if len(args) == 1:
            self.__value__ = args[0]
            self.__data__ = {"*": self.__value__}
        elif args:
            self.__value__ = list(args)
            self.__data__ = {"*": self.__value__}
        else:
            self.__value__ = None
            self.__data__ = {}

        # Handle keyword arguments safely
        for key, val in kwargs.items():
            if key in RESERVED_NAMES:
                raise TypeError(f"'{key}' is reserved and cannot be used as a keyword argument")
            setattr(self, key, val)
            self.__data__[key] = val

    def get(self):
        """Return the main value (positional arguments)."""
        return self.__value__

    def all(self):
        """Return a dictionary of all data (positional args under '*' + keywords)."""
        return self.__data__

    def __repr__(self):
        return f"<Response get={self.get()!r} all={self.all()!r}>"


class QueryBus:
    """
    Manages registering events and queries as well as triggering and
    handling them when called.
    """
    _instance_:"QueryBus" = None

    registered:dict[str, UUID] = {}
    handlers: dict[UUID, Coroutine] = {}

    @staticmethod
    def get_instance() -> "QueryBus":
        if QueryBus._instance_ is None:
            QueryBus._instance_ = QueryBus()
        return QueryBus._instance_

    # -=-=- Register and Unregister -=-=- #
    
    def register(self, query:str, handler:Coroutine) -> UUID:
        """register a handler to a query"""

    def unregister(self, id:UUID):
        """unregister an event or query"""

    # -=-=- Trigger -=-=- #

    async def query(self, query:str, data:QueryData) -> Response:
        """trigger a query"""

    # -=-=- Exists -=-=- #

    def query_exists(self, query:str) -> bool:
        """checks if a query exists"""

    def query_id_exists(self, id:UUID) -> bool:
        """checks if a query id exists"""

    def handler_exists(self, id:UUID) -> bool:
        """checks if an handler exists for a given id"""

    # -=-=- Getters and Setters -=-=- #

    def get_query_name(self, id:UUID) -> str:
        """get the query name by id"""

    def get_query_id(self, query:str) -> UUID:
        """get the query id by name"""

    def set_query_id(self, id:UUID, query:str):
        """set a query id to the current name"""
        # Note: enforce no duplicate IDs

    def remove_query_id(self, id:UUID):
        """remove the id from the active queries"""

    # -=-=- #

    def set_handler(self, id:UUID, callback:Coroutine):
        """set the handler for a defined query id"""

    def remove_handler(self, id:UUID):
        """remove the handler from a defined query id"""

    # -=-=- #


# -=-=- Main -=-=- #

if __name__ == "__main__":
    import asyncio
    from dataclasses import dataclass
    from uuid import UUID

    # Define a simple query data object
    @dataclass
    class CurrentSongQueryData:
        user: str

    # Optional: subclass if you use QueryData base
    class CurrentSongQuery(QueryData):
        user: str

    # Optional: type checking class if you use Response base
    class SongResponse(Response):
        # TODO - see about static typing the response from .get()
        user:str
        song:str


    # Define the query handler
    async def current_song_handler(query: CurrentSongQuery) -> Response:
        # Return a Response object
        song = "Silksong"
        msg = msg
        return Response(msg, user=query.user, song=song)

    async def main():
        bus = QueryBus.get_instance()

        # Register the handler
        query_id = bus.register("get_current_song", current_song_handler)

        # Query the bus
        # result: Response = await bus.query("get_current_song", CurrentSongQueryData(user="Hornet"))
        result: SongResponse = await bus.query("get_current_song", CurrentSongQueryData(user="Hornet"))

        #tmp response
        # result: Response = Response(f"Hornet's current song is Silksong", user="Hornet", song="Silksong")
        result: SongResponse = Response(f"Hornet's current song is Silksong", user="Hornet", song="Silksong")
        
        # Access using our new Response API
        print(result)             # <Response get="Hornet's current song is Silksong" all={'*': "Hornet's current song is Silksong", 'user': 'Hornet', 'song': 'Silksong'}>
        print(result.get())       # "Hornet's current song is Silksong"
        print(result.all())       # {'*': "Hornet's current song is Silksong", 'user': 'Hornet', 'song': 'Silksong'}
        print(result.user)        # "Hornet"
        print(result.song)        # "Silksong"

        # Cleanup
        bus.unregister(query_id)

    asyncio.run(main())

# EOF #
