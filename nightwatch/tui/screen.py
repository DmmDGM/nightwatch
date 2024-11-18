# Copyright (c) 2024 iiPython

# Modules
import re
import typing
from asyncio import Queue
from dataclasses import dataclass

from nightwatch.tui import HEX_COLOR

# Handle events
@dataclass
class MessageAuthor:
    name: str
    color: str

@dataclass
class MessageEvent:
    author: MessageAuthor
    message: str

@dataclass
class KeypressEvent:
    text: str

@dataclass
class ScreenEvent:
    event_type: typing.Literal["message", "keypress", "shutdown"]
    event_data: MessageEvent | KeypressEvent | None

# Handle screen
class Screen:
    def __init__(self) -> None:
        self.queue = Queue()

    def queue_event(self, event: ScreenEvent) -> None:
        self.queue.put_nowait(event)

    async def process_task(self) -> None:
        print("\033[2J\033[H", end = "")
        while True:
            event = await self.queue.get()

            # Make this code not suck
            data = event.event_data

            # Handle event types
            match event.event_type:
                case "message":
                    name, color = data.author.name, data.author.color

                    # Convert user color from HEX to RGB
                    if re.match(HEX_COLOR, color):
                        r = int(color[0:2], 16)
                        g = int(color[2:4], 16)
                        b = int(color[4:6], 16)

                    else:
                        r, g, b = 255, 255, 255

                    print(f"\033[38;2;{r};{g};{b}m{name}\033[0m: {event.event_data.message}")

                case "shutdown":
                    return

            self.queue.task_done()

screen = Screen()
