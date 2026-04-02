#! /usr/bin/env python3

# give the bot AI capabilities. 

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
import enum
from typing import Any, Callable

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio
import mido


# -=-=- Functions & Classes -=-=- #


# -=-=- Config Class -=-=- #

@configclass
class MidiConfig(ConfigClass):
    input_port: str | None = None
    output_port: str | None = None
    virtual_input: bool = False
    virtual_output: bool = False
    echo_input_to_output: bool = False
    clock:int = 100 # in htz

    @property
    def delay(self) -> float:
        return 1.0 / self.clock

# -=-=- Data Classes -=-=- #

@dataclass
class MidiMessageData:
    message: mido.Message
    data: dict = None
    port: str | None = None


@dataclass
class MidiNoteData:
    note: int
    velocity: int = 127
    channel: int = 0


@dataclass
class MidiControlChangeData:
    control: int
    value: int
    channel: int = 0


@dataclass
class MidiProgramChangeData:
    program: int
    channel: int = 0

# -=-=- Service Class -=-=- #

@serviceclass("midi")
class MidiService(BaseService[MidiConfig]):
    input_port = None
    output_port = None
    input_task: asyncio.Task = None
    running:bool = False

    event_bus:EventBus = EventBus.get_instance()

    async def start(self):
        print(f"Starting MIDI Service")
        self.running = True

        # -=- Open MIDI Input -=- #

        try:
            self.input_port = mido.open_input(
                self.config.input_port,
                virtual=self.config.virtual_input
            )
        except Exception as ex:
            print(f"Failed to open MIDI input '{self.config.input_port}': {ex}")
            self.input_port = None

        # -=- Open MIDI Output -=- #

        try:
            self.output_port = mido.open_output(
                self.config.output_port,
                virtual=self.config.virtual_output
            )
        except Exception as ex:
            print(f"Failed to open MIDI output '{self.config.output_port}': {ex}")
            self.output_port = None

        # -=- Start Input Poll Loop -=- #

        if self.input_port:
            self.input_task = asyncio.create_task(self._input_loop())

    async def stop(self):
        print("Stopping MIDI Service")
        self.running = False

        # -=- Stop Input Task -=- #

        if self.input_task:
            self.input_task.cancel()

            try:
                await self.input_task
            except asyncio.CancelledError:
                pass

        # -=- Close Ports -=- #

        if self.input_port:
            self.input_port.close()
            self.input_port = None

        if self.output_port:
            self.output_port.close()
            self.output_port = None
    
    # -=-=- #

    def __register_events__(self, event_bus:EventBus):
        self.event_bus = event_bus
        event_bus.register("MidiSendMessage", self.event_send_message)
        event_bus.register("MidiNoteOn", self.event_note_on)
        event_bus.register("MidiNoteOff", self.event_note_off)
        event_bus.register("MidiControlChange", self.event_control_change)
        event_bus.register("MidiProgramChange", self.event_program_change)
        
    def __register_queries__(self, query_bus:QueryBus):
        query_bus.register(
            "GetMidiService",
            QueryBus.lambda_handler(lambda _: Response(self, service=self))
        )

        query_bus.register("GetMidiInputs", self.query_get_midi_inputs)
        query_bus.register("GetMidiOutputs", self.query_get_midi_outputs)

    # -=- Low Level -=- #

    async def _input_loop(self):
        while self.running and self.input_port:
            for message in self.input_port.iter_pending():
                await self.handle_input_message(message)
            await asyncio.sleep(self.config.delay)

    async def handle_input_message(self, message:mido.Message):
        # print(f"MIDI IN: {message}")

        if self.config.echo_input_to_output and self.output_port:
            self.output_port.send(message)

        await self.event_bus.emit(
            "MidiMessageIn",
            MidiMessageData(
                message=message,
                data=message.dict(),
                port=getattr(self.input_port, 'name', None)
            )
        )

    def send_message(self, message):
        if not self.output_port:
            return

        self.output_port.send(message)

    # -=- Utilities -=- #

    def note_on(self, note: int, velocity: int = 127, channel: int = 0):
        self.send_message(
            mido.Message(
                'note_on',
                note=note,
                velocity=velocity,
                channel=channel
            )
        )

    def note_off(self, note: int, velocity: int = 0, channel: int = 0):
        self.send_message(
            mido.Message(
                'note_off',
                note=note,
                velocity=velocity,
                channel=channel
            )
        )

    def control_change(self, control: int, value: int, channel: int = 0):
        self.send_message(
            mido.Message(
                'control_change',
                control=control,
                value=value,
                channel=channel
            )
        )

    def program_change(self, program: int, channel: int = 0):
        self.send_message(
            mido.Message(
                'program_change',
                program=program,
                channel=channel
            )
        )

    def pitch_bend(self, pitch: int, channel: int = 0):
        self.send_message(
            mido.Message(
                'pitchwheel',
                pitch=pitch,
                channel=channel
            )
        )

    async def play_note(
        self,
        note: int,
        duration: float = 0.25,
        velocity: int = 127,
        channel: int = 0
    ):
        self.note_on(note, velocity, channel)
        await asyncio.sleep(duration)
        self.note_off(note, 0, channel)

    # -=-=- Events -=-=- #

    async def event_send_message(self, data: MidiMessageData):
        self.send_message(data.message)

    async def event_note_on(self, data: MidiNoteData):
        self.note_on(data.note, data.velocity, data.channel)

    async def event_note_off(self, data: MidiNoteData):
        self.note_off(data.note, data.velocity, data.channel)

    async def event_control_change(self, data: MidiControlChangeData):
        self.control_change(data.control, data.value, data.channel)

    async def event_program_change(self, data: MidiProgramChangeData):
        self.program_change(data.program, data.channel)

    async def query_get_midi_inputs(self, _) -> Response:
        names = mido.get_input_names()
        return Response(names, inputs=names, service=self)
    
    async def query_get_midi_outputs(self, _) -> Response:
        names = mido.get_output_names()
        return Response(names, outputs=names, service=self)



# EOF #
