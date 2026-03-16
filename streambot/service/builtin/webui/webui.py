#! /usr/bin/env python3

"""
WebUI Service

This package provides a FastAPI-based web interface for controlling
the bot, viewing chat messages, and displaying dynamic widgets.
It integrates with the bot's EventBus to send/receive events in real-time.

File structure:
---------------
streambot/www/
    static/      -> CSS/JS/images
    pages/       -> chat.html, dashboard.html
    widgets/     -> built-in widgets
usr/widgets/     -> user-provided widgets

Modules & Subpackages:
----------------------
- webui.py      The main WebUI service class implementing the FastAPI server
                with chat, dashboard, and unified widget support.

Usage:
------
from webui.webui import WebUIService, WebUIConfig

config = WebUIConfig(host="127.0.0.1", port=13337)
webui = WebUIService(config)
await webui.start()

Access:
-------
http://127.0.0.1:13337/chat
http://127.0.0.1:13337/dashboard
http://127.0.0.1:13337/widgets/{widget_name}.html
"""

# -=-=- Imports & Globals -=-=- #
from enum import Enum
from dataclasses import dataclass
from typing import Any, List

import os
import asyncio

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from urllib.parse import parse_qs
import uvicorn

from ... import BaseService, serviceclass, ConfigClass, configclass
from ....signals import EventBus, EventData, QueryBus
# from ..chat import ChatMessageData, MessageOutData

from .widgets.manager import WidgetManager
from .widgets.bridge import EventBridge
from .widgets.base import Widget



@dataclass
class WSMessageData:
    event: str
    data: Any

@dataclass
class WSMessageOutData:
    path: str
    event: str
    message: dict[str, str]
    

# -=-=- Config Class -=-=- #
@configclass
class WebUIConfig(ConfigClass):
    """Configuration for WebUI service."""

    host: str = "127.0.0.1"
    port: int = 13337
    www_dir: str = "www"          # Base built-in www dir
    user_widgets_dir: str = "usr/widgets"  # user-provided widgets


# -=-=- Service Class -=-=- #
@serviceclass("webui")
class WebUIService(BaseService[WebUIConfig]):
    """
    FastAPI WebUI Service.

    Features:
        - Chat page for reading/sending messages
        - Dashboard page for controlling widgets & stats
        - Unified widget system for OBS/browser embedding
        - WebSocket connection to EventBus for real-time events
    """

    def __init__(self, config: WebUIConfig):
        super().__init__(config)
        self.app = FastAPI()
        self.clients: dict[str, list[WebSocket]] = {}


        self.www_dir = os.path.abspath(os.path.join('streambot', self.config.www_dir))
        self.builtin_widgets_dir = os.path.join(self.www_dir, "widgets")
        self.static_dir = os.path.join(self.www_dir, "static")
        self.pages_dir = os.path.join(self.www_dir, "pages")
        self.user_widgets_dir = os.path.abspath(self.config.user_widgets_dir)
        self.server = None
        
        # Jinja environment; loader can point to multiple folders
        self.env = Environment(
            loader=FileSystemLoader([
                # self.builtin_widgets_dir,
                # self.user_widgets_dir,
                os.path.join(self.builtin_widgets_dir),
                os.path.join(self.user_widgets_dir)
            ]),
            # autoescape=select_autoescape(['html', 'xml'])
        )
        
        self.widget_manager = WidgetManager(self.builtin_widgets_dir, self.user_widgets_dir)
        self.event_bridge = EventBridge()
        self.widget_manager.load(self.event_bridge)
        
        self.event_bus: EventBus | None = self.event_bus or EventBus.get_instance()
        self.query_bus: QueryBus | None = self.query_bus or QueryBus.get_instance()

        self.widget_manager.register_events(self.event_bus)
        self.widget_manager.register_queries(self.query_bus)    

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=self.static_dir), name="static")

        # Widget route
        self.app.get("/widget/{path:path}")(self.widget_handler)
        self.app.get("/widgets/{path:path}")(self.get_widgets_handler)

        # Page routes
        self.app.get("/chat")(self.chat_page)
        self.app.get("/dashboard")(self.dashboard_page)

        # WebSocket route
        self.app.websocket("/ws/{path:path}")(self.websocket)

    # -=-=- START/STOP -=-=- #
    async def start(self):
        """Start FastAPI server asynchronously."""
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="warning"
        )
        self.server = uvicorn.Server(config)


        asyncio.create_task(self.server.serve())
        print(f"WebUI running at http://{self.config.host}:{self.config.port}")

    async def stop(self):
        """Stop FastAPI server."""
        if self.server:
            self.server.should_exit = True
            print("WebUI stopped")

    # -=-=- PAGE HANDLERS -=-=- #
    async def chat_page(self):
        """Serve chat page."""
        path = os.path.join(self.pages_dir, "chat.html")
        return FileResponse(path)

    async def dashboard_page(self):
        """Serve dashboard page."""
        path = os.path.join(self.pages_dir, "dashboard.html")
        return FileResponse(path)
    
    # -=-=- TEMPLATE RENDERING -=-=- #

    def render_template(self, template_path: str, context: dict) -> str:
        """Render a generic template (dashboard, chat page, etc.)"""
        tmpl = self.env.get_template(template_path)
        return tmpl.render(**context)

    def render_widget_template(self, widget_name: str, template_name: str, context: dict) -> str:
        """
        Render a widget template.
        Priority: builtin -> user
        """
        builtin_path = os.path.join(self.builtin_widgets_dir, widget_name, "templates", template_name)
        user_path = os.path.join(self.user_widgets_dir, widget_name, "templates", template_name)

        if os.path.isfile(builtin_path) or os.path.isfile(user_path):
            path = os.path.join(widget_name, "templates", template_name).replace("\\", "/")
        else:
            raise FileNotFoundError(f"Template {template_name} for widget {widget_name} not found")

        return self.render_template(path, context)

    # -=-=- WIDGET HANDLER -=-=- #
    async def widget_handler(self, path: str, request: Request):
        """
        Serve widgets dynamically.
        e.g. /widgets/chat/onscreenchat?style=tech
        """
        path_parts = path.split("/")
        widget_name = path_parts[0]
        view = path_parts[1] if len(path_parts) > 1 else None

        widget: Widget = self.widget_manager.get_widget(widget_name)
        if widget is None:
            raise HTTPException(status_code=404, detail=f"Widget '{widget_name}' not found")
        
        # print(  f"Widget request: {widget_name}, view: {view}, query: {request.query_params}")

        # Parse query parameters
        query_params = dict(request.query_params)

        template_name = f"{view}.html" if view else f"widget.html"

        context = widget.context().copy()
        context.update(query_params)
        context["base_url"] = f"/widget/{widget_name}"

        if '.' not in path.split("/")[-1]:
            html = self.render_widget_template(widget_name, template_name, context)
            return HTMLResponse(html)
        
        # For JS/CSS files, fall back to FileResponse
        builtin_path = os.path.join(self.builtin_widgets_dir, path)
        if os.path.isfile(builtin_path):
            return FileResponse(builtin_path)

        user_path = os.path.join(self.user_widgets_dir, path)
        if os.path.isfile(user_path):
            return FileResponse(user_path)

        raise HTTPException(status_code=404, detail=f"Widget file '{path}' not found")
    
    async def get_widgets_handler(self, path: str):
        """Return a JSON list of available widgets."""

        if path == "":
            widgets = self.widget_manager.widgets
            widget_names = [w.name for w in widgets]
            return widget_names
        
        if path == "active":
            widgets = self.widget_manager.widgets
            active_widgets = [w.name for w in widgets if w.active]
            return active_widgets

    # -=-=- WEBSOCKET HANDLING -=-=- #
    async def websocket(self, ws: WebSocket, path: str):
        await ws.accept()
        self.clients.setdefault(path, []).append(ws)
        print("WebUI client connected")

        try:
            while True:
                data = await ws.receive_json()
                await self.handle_client_message(path, data)
        except WebSocketDisconnect:
            print("WebUI client disconnected")
            self.clients.get(path, []).remove(ws)
        except Exception as e:
            print("WebUI websocket error:", e)
            self.clients.get(path, []).remove(ws)

    async def handle_client_message(self, path: str, msg: dict):
        """Handle incoming messages from browser."""
        event = msg.get("event")
        data = msg.get("data", {})

        print(f"WebUI received messagefor widget {path}: {event}, data: {data}")

        await self.event_bus.emit("WSMessage", WSMessageData(event=event, data=data))
        await self.event_bus.emit(f"WSMessage{path.title()}", WSMessageData(event=event, data=data))

    async def broadcast(self, data: WSMessageOutData):
        """Send data to all connected WebSocket clients."""
        for ws in list(self.clients.get(data.path, [])):
            try:
                await ws.send_json(data.__dict__)
            except:
                self.clients.get(data.path, []).remove(ws)

    # -=-=- EVENT REGISTRATION -=-=- #
    def __register_events__(self, event_bus: EventBus):
        """Register EventBus events for chat and widget updates."""
        self.event_bus = event_bus
        event_bus.register("WSMessageOut", self.broadcast)


    #     self.event_bridge.register_events(event_bus)
    #     self.widget_manager.register_events(event_bus)

    def __register_queries__(self, query_bus: QueryBus):
        """Register QueryBus queries for widget data retrieval."""
        self.query_bus = query_bus

    #     self.event_bridge.register_queries(query_bus)
    #     self.widget_manager.register_queries(query_bus)


# -=-=- DISPLAY DATA TYPES -=-=- #
class DisplayMessageType(Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


@dataclass
class DisplayOutData(EventData):
    message: str
    type: DisplayMessageType = DisplayMessageType.INFO