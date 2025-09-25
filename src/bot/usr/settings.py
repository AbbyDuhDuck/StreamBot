

from .events import UserEvents, DefaultEvents
from .commands import UserCommands, DefaultCommands

class UserSettings:
    name:str
    account_user:str
    account_bot:str|None

    commands:UserCommands=DefaultCommands
    events:UserEvents=DefaultEvents

    def __init__(
            self,
            name:str,
            account_user:str,
            account_bot:str|None=None,
            # commands:UserCommands=DefaultCommands,
            # events:UserEvents=DefaultEvents,
    ):
        self.name = name
        self.account_user = account_user
        self.account_bot = account_bot

    def run(self):
        self.commands = self.commands(self)
        self.events = self.events(self)

