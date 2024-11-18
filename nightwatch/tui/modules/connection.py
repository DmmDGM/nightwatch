# Copyright (c) 2024 iiPython

# Modules
import asyncio

import orjson
from readchar import readkey, key
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from nightwatch.tui import config
from nightwatch.tui.screen import (
    screen,
    ScreenEvent, MessageEvent, MessageAuthor
)

async def handle_keypresses(screen, websocket) -> None:
    while True:
        loop = asyncio.get_event_loop()
        match await loop.run_in_executor(None, readkey):
            case key.BACKSPACE if screen.input_buffer:
                screen.input_buffer = screen.input_buffer[:-1]

            case key.ENTER:
                await websocket.send(orjson.dumps({"type": "message", "data": {"text": screen.input_buffer}}))
                screen.input_buffer = ""

            case character:
                screen.input_buffer += character
        
        screen.queue_event(ScreenEvent("keypress", None))

async def establish_connection(host: str, port: int) -> None:
    async with connect(f"ws{'s' if port == 443 else ''}://{host}:{port}/gateway") as websocket:

        # Send identification payload
        await websocket.send(orjson.dumps({
            "type": "identify",
            "data": {
                "name": config["username"],
                "color": config["color"]
            }
        }), text = True)

        # Handle our screen
        screen_task = asyncio.create_task(screen.process_task())

        # Handle keypresses
        _ = asyncio.create_task(handle_keypresses(screen, websocket))

        # Stop this dumbass thread from exiting
        while True:
            try:
                message = orjson.loads(await websocket.recv())
                # screen.queue_event(ScreenEvent("message", MessageEvent(MessageAuthor("Internal", "ffffff"), str(message))))
                match message["type"]:
                    case "message":
                        screen.queue_event(ScreenEvent("message", MessageEvent(
                            MessageAuthor(**message["data"]["user"]),
                            message["data"]["text"]
                        )))

            except ConnectionClosed:
                print("Connection terminating.")
                screen.queue_event(ScreenEvent("shutdown", None))
                await screen_task
                break

        # See what the fuck Nightwatch says
        # message = await websocket.recv()
        # print(message)
