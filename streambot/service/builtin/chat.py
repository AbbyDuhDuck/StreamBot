# general chat stuff

# Urgent


from enum import Enum
from dataclasses import dataclass

from ...signals import EventBus, EventData, QueryBus, QueryData, Response


class Platform(Enum):
    TWITCH = "Twitch"
    YOUTUBE = "YouTube"
    DISCORD = "Discord"

class UserType(Enum):
    USER = "User"
    BOT = "Bot"

@dataclass
class ChatMessageData(EventData):
    message:str
    user:str
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False

@dataclass
class MessageOutData(EventData):
    message:str
    user_type:UserType = UserType.BOT
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False
