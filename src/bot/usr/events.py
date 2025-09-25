from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from .settings import UserSettings

class UserEvents:
    def __init__(self, settings:"UserSettings"):
        self.settings = settings
        self.__register_events__()

    def __register_events__(self):
        pass
        # add a raised error


class DefaultEvents(UserEvents):
    def __init__(self, settings:"UserSettings"):
        super().__init__(settings)

    @override
    def __register_events__(self):
        print('Registering Default Events')