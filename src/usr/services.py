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

from ..service import BaseService, SERVICE_REGISTRY

# -=-=- Classes -=-=- #

class UserServices:
    """manages the services for users"""
    active:dict[str, BaseService] = {}
    registered:dict[str, type[BaseService]] = {}

    def __init__(self):
        self.active:dict[str, BaseService] = {}
        self.registered:dict[str, type[BaseService]] = SERVICE_REGISTRY.copy()

    def enable(self, name:str, config:Any|None = None, **kwargs):
        if name not in self.registered:
            raise ValueError(f"Unknown Service: {name}")
        
        service_class:type[BaseService] = self.registered[name]
        service = service_class(config)
        service.configure(service.Config(**kwargs))
        self.active[name] = service

    async def disable(self, name:str):
        if name not in self.active:
            raise ValueError(f"Not active service: {name}")
        await self.stop(name)
        del self.active[name]

    def configure(self, name:str, config:Any|None = None, **kwargs):
        if name not in self.active:
            raise ValueError(f"Not active service: {name}")
        
        service:BaseService = self.active[name]
        if config: service.configure(config)
        if kwargs: service.configure(service.Config(**kwargs))

    def get_config(self, name:str) -> Any:
        if name not in self.registered:
            raise ValueError(f"Unknown Service: {name}")
            # raise ValueError(f"Not active service: {name}")

        return self.registered[name].Config

    async def start(self, name:str):
        if name not in self.active:
            raise ValueError(f"Not active service: {name}")
        await self.active[name].start()

    async def stop(self, name:str):
        if name not in self.active:
            raise ValueError(f"Not active service: {name}")
        await self.active[name].stop()

    async def start_all(self):
        for svc in self.active.values():
            await svc.start()
    
    async def stop_all(self):
        for svc in self.active.values():
            await svc.stop()


    def register(self, name:str, service:type[BaseService]):
        """Register a service"""
        self.registered[name] = service


# -=-=- MAIN (for testing) -=-=- #

async def main():
    
    # -=-=- TMP Imports -=-=- #

    from ..service import ConfigClass, configclass, serviceclass, BaseService

    # -=-=- Config Class -=-=- #

    @configclass
    class OBSConfig:#(ConfigClass):
        host: str = "localhost"
        port: int = 4455
        password: str|None = None

    obs_config = OBSConfig(host="192.168.1.1")
    print(obs_config)

    obs_config = obs_config.replace(OBSConfig(port=9999))
    print(obs_config)

    obs_config = obs_config.replace(OBSConfig("localhost", password="PASSword"))
    print(obs_config)


    # -=-=- Service Class -=-=- #

    # @serviceclass
    # @serviceclass()
    @serviceclass("obs")
    # @serviceclass(name="obs")
    class OBSService(BaseService[OBSConfig]):
        async def start(self):
            print(f"Starting OBS at {self.config.host}:{self.config.port} -- pass:{self.config.password}")

        async def stop(self):
            print("Stopping OBS")

    obs_service = OBSService(obs_config)
    obs_service.configure(obs_service.Config("192.168.1.1"))
    await obs_service.start()
    await obs_service.stop()

    user_services = UserServices()
    user_services.enable('obs', OBSConfig(port=9999), host="0.0.0.0")
    user_services.configure('obs', password="something")
    user_services.configure('obs', user_services.get_config('obs')(host='localhost'))

    await user_services.start_all()
    await user_services.stop_all()

    await user_services.disable('obs')

    user_services.enable('obs', user_services.get_config('obs')(port=1234))
    await user_services.start('obs')
    await user_services.stop_all()


if __name__ == '__main__':
    asyncio.run(main())

# EOF #