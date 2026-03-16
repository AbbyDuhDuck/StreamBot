from typing import Type, Iterable, Any, Callable

from attr import dataclass

from .bridge import EventBridge
from streambot.signals.event_bus import EventBus
from streambot.signals.query_bus import QueryBus


class Widget:
    """
    Base class for widgets.
    """

    EVENTS: Iterable[Type] = ()
    QUERIES: Iterable[Type] = ()

    TEMPLATE = "widget.html"

    active: bool = False

    def __init__(self):
        self.api:EventBridge = None
        self.name = None
        self.path = None

    # ------------------------------------------------
    # Lifecycle
    # ------------------------------------------------

    def register_events(self, event_bus:EventBus):
        pass
    
    def register_queries(self, query_bus:QueryBus):
        pass    

    # ------------------------------------------------
    # Core registration primitive
    # ------------------------------------------------

    def register(self, event: str, handler: Callable):
        self.api.register(event, handler)

    def emit(self, event: str, **data: Any):
        self.api.emit(event, **data)

    async def query(self, query_type: Type, **data: Any):
        return await self.api.query(query_type, **data)

    # ------------------------------------------------
    # Websocket helpers
    # ------------------------------------------------

    def ws_event(self, event_type: Type):
        """
        Returns a handler tuple usable with register().
        """

        async def handler(event):
            await self.api.send_ws(event)

        return (event_type, handler)

    def ws_register(self, event_type: Type):
        """
        Convenience wrapper for websocket passthrough.
        """
        self.register(*self.ws_event(event_type))

    # ------------------------------------------------
    # Rendering
    # ------------------------------------------------

    def context(self) -> dict:
        return {}