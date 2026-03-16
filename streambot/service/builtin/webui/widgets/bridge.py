import dataclasses
from typing import Callable
from streambot.signals import EventBus, QueryBus, EventData, QueryData, Response

class EventBridge:

    def __init__(self):

        self.event_bus = EventBus.get_instance()
        self.query_bus = QueryBus.get_instance()

        self.websocket_send = None

    # ------------------------------------------------
    # Websocket connection
    # ------------------------------------------------

    def attach_websocket(self, sender):
        """
        sender(payload: dict)
        """
        self.websocket_send = sender

    async def send_ws(self, data: dict):

        if not self.websocket_send:
            print("Websocket sender not attached to EventBridge")
            return

        await self.websocket_send(data)

    # ------------------------------------------------
    # Emit
    # ------------------------------------------------

    def emit(self, event: str, data: EventData):

        self.event_bus.emit(event, data)

    # ------------------------------------------------
    # Subscribe
    # ------------------------------------------------

    def register(self, event: str, handler: Callable):

        self.event_bus.register(event, handler)

    # ------------------------------------------------
    # Query
    # ------------------------------------------------

    async def query(self, query: str, data: QueryData) -> dict:

        result = await self.query_bus.query(query, data)

        if dataclasses.is_dataclass(result):
            return dataclasses.asdict(result)

        return result

    # ------------------------------------------------
    # Websocket incoming events
    # ------------------------------------------------

    # def handle_ws(self, event:str, data):

    #     event = event_type(**data)

    #     self.event_bus.emit(event)