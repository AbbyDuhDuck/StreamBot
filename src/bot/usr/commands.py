from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from .settings import UserSettings

class UserCommands:
    def __init__(self, settings:"UserSettings"):
        self.settings = settings
        self.__register_commands__()

    def __register_commands__(self):
        pass
        # add a raised error


class DefaultCommands(UserCommands):
    def __init__(self, settings:"UserSettings"):
        super().__init__(settings)

    @override
    def __register_commands__(self):
        print('Registering Default Commands')