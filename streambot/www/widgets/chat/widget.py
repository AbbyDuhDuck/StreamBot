#! /usr/bin/env python3

"""Chat widget for the WebUI."""

from streambot.service.builtin.webui.webui import WSMessageData, WSMessageOutData
from streambot.service.builtin.webui.widgets import base
from streambot.service.builtin.chat import ChatMessageData, ChatNotificationData, MessageOutData, Platform
from streambot.service.builtin.commands import parse_command, ChatCommandData
from streambot.signals.event_bus import EventBus


PLATFORM_TWITCH_ICON = '<i class="fa fa-twitch"></i>'
PLATFORM_YOUTUBE_ICON = '<i class="fa fa-youtube-play"></i>'
PLATFORM_UNKNOWN_ICON = '<i class="fa fa-question-circle"></i>'

BROADCASTER_BADGE_URL = 'https://static-cdn.jtvnw.net/badges/v1/5527c58c-fb7d-422d-b71b-f309dcb85cc1/1'
BROADCASTER_BADGE_ICON = f'<img src="{BROADCASTER_BADGE_URL}" alt="HEAD-MOD" class="badge">'
HEADMOD_BADGE_URL = 'https://assets.help.twitch.tv/article/img/000002212-07.png'
HEADMOD_BADGE_ICON = f'<img src="{HEADMOD_BADGE_URL}" alt="HEAD-MOD" class="badge">'
MOD_BADGE_URL = 'https://static-cdn.jtvnw.net/badges/v1/3267646d-33f0-4b17-b3df-f923a41db1d0/1'
MOD_BADGE_ICON = f'<img src="{MOD_BADGE_URL}" alt="MOD" class="badge">'
VIP_BADGE_URL = 'https://static-cdn.jtvnw.net/badges/v1/b817aba4-fad8-49e2-b88a-7cc744dfa6ec/1'
VIP_BADGE_ICON = f'<img src="{VIP_BADGE_URL}" alt="VIP" class="badge">'

def get_platform_icon(platform:Platform) -> str:
    if platform is Platform.TWITCH: return PLATFORM_TWITCH_ICON
    if platform is Platform.YOUTUBE: return PLATFORM_YOUTUBE_ICON
    return PLATFORM_UNKNOWN_ICON

def get_badges(event:ChatMessageData) -> str:
    result = ""
    if event.has_broadcaster: return BROADCASTER_BADGE_ICON
    # -=-=- #
    if event.has_head_mod: result += HEADMOD_BADGE_ICON
    elif event.has_mod: result += MOD_BADGE_ICON
    
    if event.has_vip: result += VIP_BADGE_ICON
    return result

class Widget(base.Widget):
    name = "chat"
    display_name = "Chat"
    description = "Displays chat messages from Twitch and YouTube."

    active = True

    event_bus: EventBus | None = EventBus.get_instance()
    
    EVENTS = [ChatMessageData, ChatNotificationData, WSMessageData, WSMessageOutData]

    def register_events(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.register("WSMessageChat", self.event_ws_message)
        self.register("ChatMessage", self.event_chat_message)
        self.register("ChatNotification", self.event_chat_notification)

    async def event_ws_message(self, event:WSMessageData):
        # print(f"Received WSMessage ({event.event}): {event.data}")
        if event.event == "message":
            message:str = event.data.get("message", "")
            if message.startswith("!"):
                cmd, args = parse_command(message)
                await self.event_bus.emit("ChatCommand", ChatCommandData(command=cmd, args=args, user="AbbyDuhDuck"))
            else:
                await self.event_bus.emit("MessageOut", MessageOutData(message=message))

    async def event_chat_message(self, event:ChatMessageData):
        # print(f"ChatMessage: {event.user}: {event.message} [{event.timestamp}]")
        # print("Emotes:", event.emotes)
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="chat", event="chat-message", message={
            "message": event.message,
            "user": event.user,
            "platform": event.platform.value.lower(),
            "platform_icon": get_platform_icon(event.platform),
            "badges": get_badges(event),
            "color": event.user_color,
            "has_ads": event.has_ads,
            "emotes": event.emotes
        }))
    async def event_chat_notification(self, event:ChatNotificationData):
        print(f"Chat Notif ({event.type}): {event.message}")
        await self.event_bus.emit("WSMessageOut", WSMessageOutData(path="chat", event="chat-notification", message={
            "message": event.message,
            "type": event.type.value.lower()
        }))

