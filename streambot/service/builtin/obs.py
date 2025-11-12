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

from abc import ABC, abstractmethod
from typing import override
from dataclasses import dataclass, fields, replace, field
from typing import TypeVar, Self, Any, Type, Callable, Generic
from functools import wraps
import asyncio

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #

@configclass
class OBSConfig(ConfigClass):
    host: str = "localhost"
    port: int = 4455
    password: str|None = None


# -=-=- Service Class -=-=- #


# import secret
import asyncio
import obsws_python as obs
import socket


# -=-=- Function -=-=- #

def check_socket(host,port,timeout=2):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #presumably 
    sock.settimeout(timeout)
    try:
       sock.connect((host,port))
    except:
       return False
    else:
       sock.close()
       return True


# -=-=- Classes -=-=- #

@serviceclass("obs")
class OBSService(BaseService[OBSConfig]):
    _connected = False
    client:obs.ReqClient = None

    async def start(self):
        print(f"Starting OBS at {self.config.host}:{self.config.port} -- pass:{self.config.password}")

    async def stop(self):
        print("Stopping OBS")

    # -=-=- #
    
    @property
    def connected(self) -> bool:
        return self._connected and self.client is not None

    def connect(self):
        if self.connected: return
        if not check_socket(host=self.config.host, port=self.config.port):
            print("Failed to connect to OBS")
            return
        # -=-=- #
        self.client:obs.ReqClient = obs.ReqClient(host=self.config.host, port=self.config.port, password=self.config.password, timeout=3)
        self._connected = True
        
    def check_connection(self) -> bool:
        self.connect()
        return self.connected
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register('OBSMute', EventBus.lambda_action(lambda _: self.mute_mic()))
        event_bus.register('OBSUnmute', EventBus.lambda_action(lambda _: self.unmute_mic()))
        
        event_bus.register('OBSEnableItem', self.event_set_item_enabled)
        event_bus.register('OBSDisableItem', self.event_set_item_disabled)
        
    def __register_queries__(self, query_bus):
        query_bus.register(
            'GetServiceOBS', 
            QueryBus.lambda_handler(lambda _: Response(self, service=self))
        )
        query_bus.register(
            'GetClientOBS', 
            QueryBus.lambda_handler(lambda _: Response(self.client, client=self.client))
        )

        query_bus.register('OBSGetItemID', self.event_get_item_id)

    # -=-=- #

    def mute_mic(self):
        if not self.check_connection(): return
        # -=-=- #
        self.client.set_input_mute("Mic/Aux", True)
        
    def unmute_mic(self):
        if not self.check_connection(): return
        # -=-=- #
        self.client.set_input_mute("Mic/Aux", False)

    # -=-=- #

    def get_item_id(self, scene:str, item:str) -> int:
        if not self.check_connection(): return None
        scene_item = self.client.get_scene_item_id(scene, item)
        return scene_item.scene_item_id if scene_item else None
    
    def set_item_enabled(self, scene:str, id:int, enable:bool=True):
        if not self.check_connection(): return None
        self.client.set_scene_item_enabled(scene, id, enable)

    # -=-=- Events -=-=- #

    async def event_set_item_enabled(self, data:"EnabledItemData"):
        self.set_item_enabled(data.scene, data.id, data.enable)
        
    async def event_set_item_disabled(self, data:"EnabledItemData"):
        self.set_item_enabled(data.scene, data.id, False)

    async def event_get_item_id(self, data:"GetItemIDData") -> "GetItemIDResponse":
        id = self.get_item_id(data.scene, data.item)
        return GetItemIDResponse(scene=data.scene, id=id)


class GetItemIDData(QueryData):
    scene:str
    item:str

class GetItemIDResponse(Response):
    scene:str
    id:int

class EnabledItemData(EventData):
    scene:str
    id:int
    enable:bool=True


# EOF #
