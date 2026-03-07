# GUI 

# Urgent

from attr import dataclass
from enum import Enum

from ...signals import EventBus, EventData, QueryBus, QueryData, Response

class DisplayMessageType(Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"

@dataclass
class DisplayOutData(EventData):
    message:str
    type:DisplayMessageType = DisplayMessageType.INFO