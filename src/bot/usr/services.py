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


# -=-=- Registry -=-=- #


SERVICE_REGISTRY: dict[str, type["BaseService"]] = {}

def register(name: str):
    def _decorator(cls):
        SERVICE_REGISTRY[name] = cls
        return cls
    return _decorator

def get_service(name: str):
    return SERVICE_REGISTRY.get(name)


# -=-=- Decorators -=-=- #

def track_args(cls):
    """
    Decorator that wraps the class __init__ to track which arguments were
    explicitly provided during instantiation.

    Positional and keyword arguments are recorded in `__provided_fields__`.
    """
    __init__ = cls.__init__

    @wraps(__init__)
    def init(self, *args, **kwargs):
        # make a set of field names that were given
        self.__provided_fields__ = set(kwargs.keys())
        # handle positional args
        for name, _ in zip([field.name for field in fields(cls)], args):
            self.__provided_fields__.add(name)
        # call the normal init
        __init__(self, *args, **kwargs)
    
    cls.__init__ = init
    return cls


def configclass(cls):
    """
    Decorator for dataclass-based configuration classes.

    Adds a `replace` method that allows replacing only the explicitly
    provided fields from another instance of the same class.
    """
    # Additionally decorates the class with @track_args and @dataclass
    # decorators.
    
    # inject replace method
    def _replace(self, config:Self) -> Self:
        """thing"""
        if not isinstance(config, type(self)):
            raise TypeError(f'Expected {type(self)} instance, got {type(config)} instead.')
        # -=-=- #
        fields = {field:getattr(config,field) for field in config.__provided_fields__}
        return replace(self, **fields)
    cls.replace = _replace
    # decorate class
    cls = dataclass(cls)
    cls = track_args(cls)
    return cls


# -=-=- Classes -=-=- #


class ConfigClass:
    """
    Base class for configuration objects.

    Intended to be used with the @configclass decorator. Provides type
    annotations for `replace` and `__provided_fields__`.
    """
    
    __provided_fields__: list[str]

    def replace(self, config:Self) -> Self:
        """Return a new instance with fields updated from `config`; raises TypeError if type mismatched."""
        ...

C = TypeVar("C", bound=ConfigClass)

def serviceclass(arg=None, *, name:str|None=None):
    """
    Decorator for defining a service class. 
    If `name` is provided, the service is automatically registered.
    
    Can be used as:
      @serviceclass
      class MyService: ...

    or:
      @serviceclass()
      class MyService: ...

    or:
      @serviceclass("name")
      class MyService: ...

    or:
      @serviceclass(name="name")
      class MyService: ...

    """
    # correct for positional arg passed like @serviceclass("name")
    if isinstance(arg, str):
        name = arg
        arg = None
    # -=-=- #
    def wrap(cls):
        # add the Config type for its definition
        config_type = getattr(cls, "__orig_bases__", [None])[0].__args__[0]
        cls.Config = config_type
        # register the class if name is provided 
        if name: register(name)(cls)
        # -=-=- #
        return cls
    # Allow decorator to be used with or without parentheses
    if arg is None:
        return wrap
    else:
        return wrap(arg)


class BaseService(ABC, Generic[C]):
    """Abstract Service Base Class for internal and user defined services to build upon"""

    Config:C

    def __init__(self, config:C|None = None):
        self.config:C = config or self.Config()

    def configure(self, config:C):
        """Update the service's config."""
        self.config = self.config.replace(config)
    
    @abstractmethod
    async def start(self): ...

    @abstractmethod
    async def stop(self): ...

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