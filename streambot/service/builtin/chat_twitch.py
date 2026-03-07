# twitch chat service.

# Urgent

from enum import Enum
from dataclasses import dataclass

from ...signals import EventBus, EventData, QueryBus, QueryData, Response


@dataclass
class SetGameData(EventData):
    game:str
