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

from dataclasses import dataclass

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response


# -=-=- Functions & Classes -=-=- #

# -=-=- Config Class -=-=- #

@configclass
class SoundConfig(ConfigClass):
    tts_filename: str = "tts"


# -=-=- Service Class -=-=- #


import pyttsx3
from pygame import mixer, _sdl2 as devices
from os.path import exists as path_exists
from os import remove as path_remove

import asyncio


# -=-=- Function -=-=- #



# -=-=- Classes -=-=- #

@serviceclass("sound")
class SoundService(BaseService[SoundConfig]):
    queue:list[str] = []
    sound_effects:dict[str, mixer.Sound] = {}
    engine: pyttsx3.Engine

    main_task: asyncio.Task

    def __init__(self, config:SoundConfig):
        super().__init__(config)

        # Old Code:
        # engine = pyttsx3.init()
        # engine.setProperty('rate', 135)
        # voices = engine.getProperty('voices')
        # print(voices)
        # engine.setProperty('voice', voices[1].id)
        # -=-=- #

        # New Code:
        # Get available output devices
        # mixer.init()
        # print("Outputs:", )
        # for thing in devices.audio.get_audio_device_names(False): print(thing)
        # mixer.quit()

        # Initialize mixer with the correct device
        # Set the parameter devicename to use the VB-CABLE name from the outputs printed previously.
        # mixer.init(devicename = "CABLE Input (VB-Audio Virtual Cable)")
        
        mixer.init()
        # mixer.init(devicename = "Voicemeeter Input (VB-Audio Voicemeeter VAIO)")

        # Initialize text to speech
        engine = pyttsx3.Engine()
        
        engine.setProperty('rate', 135)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        # print(voices)

        self.engine = engine


    async def start(self):
        print(f"Starting Sound Service")
        self.main_task = asyncio.create_task(self.main())

    async def stop(self):
        print("Stopping Sound Service")
        self.main_task.cancel()
        try:
            await self.main_task
        except asyncio.CancelledError:
            pass
        print("Sound Service Fully Stopped")

    async def main(self):
        while True:
            await asyncio.sleep(1)
            if len(self.queue) == 0: continue
            if mixer.music.get_busy(): continue
            # -=-=- #
            msg = self.queue.pop(0)
            self.play_tts(msg)
    
    # -=-=- #

    def __register_events__(self, event_bus:EventBus):
        # event_bus.register("BotStop", self.event_on_stop)
        event_bus.register("PlayTTS", self.event_play_tts)
        event_bus.register("PlaySFX", self.event_play_sfx)
        
    def __register_queries__(self, query_bus:QueryBus):
        query_bus.register(
            'GetSoundService', 
            QueryBus.lambda_handler(lambda _: Response(self, service=self))
        )

    # -=-=- #

    def add_sfx(self, name: str, file: str, volume:float = 1):
        sound = mixer.Sound(file)
        sound.set_volume(volume)
        self.sound_effects[name] = sound

    async def play_sfx(self, name: str):
        if name not in self.sound_effects:
            return
        # -=-=- #
        self.sound_effects[name].play()
    
    # -=-=- #

    def queue_tts(self, msg):
        self.queue.append(msg)
    
    def play_tts(self, msg):
        # self.engine.say(msg)
        # self.engine.runAndWait()
        # return

        filepath = "tmp/{filename}.wav".format(filename=self.config.tts_filename)

        # if file exists then remove!!!
        mixer.music.unload()
        if path_exists(filepath):
            path_remove(filepath)
    
        # Save speech as audio file
        self.engine.save_to_file(msg, filepath)
        self.engine.runAndWait()

        # Play the saved audio file
        mixer.music.load(filepath)
        mixer.music.play()

    # -=-=- Events -=-=- #

    async def event_play_tts(self, data:"PlayTTSData"):
        self.queue_tts(data.message)
    
    async def event_play_sfx(self, data:"PlaySFXData"):
        if data.name not in self.sound_effects:
            return
        # -=-=- #
        self.sound_effects[data.name].play()


@dataclass
class PlayTTSData(EventData):
    message:str

@dataclass
class PlaySFXData(EventData):
    name:str

# EOF #
