# service is means of hooking into other APIs like twitch and youtube and OBS

from ..events import event

def service():
    event('service thing!!')
