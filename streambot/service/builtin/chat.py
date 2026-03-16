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
class ChatNotificationData(EventData):
    message:str

@dataclass
class ChatMessageData(EventData):
    # message
    message:str
    user:str
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False
    # user
    has_broadcaster:bool = False
    has_head_mod:bool = False
    has_mod:bool = False
    has_vip:bool = False
    has_ads:bool = True
    user_color: str = "#ccc"


@dataclass
class MessageOutData(EventData):
    message:str
    user_type:UserType = UserType.BOT
    platform:Platform = Platform.TWITCH
    shared_chat:bool = False
