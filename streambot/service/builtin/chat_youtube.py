# youtube chat service.

# Urgent

from enum import Enum
from dataclasses import dataclass

from ...signals import EventBus, EventData, QueryBus, QueryData, Response


@dataclass
class SetYouTubeIDData(EventData):
    youtube_id:str
