# Copyright (c) 2024 iiPython

# Modules
import asyncio

import orjson
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from nightwatch.tui import config
from nightwatch.tui.screen import (
    screen,
    ScreenEvent, MessageEvent, MessageAuthor
)

async def establish_connection(host: str, port: int) -> None:
    async with connect(f"ws{'s' if port == 443 else ''}://{host}:{port}/gateway") as websocket:

        # Send identification payload
        await websocket.send(orjson.dumps({
            "type": "identify",
            "data": {
                "name": config["username"],
                "color": f"#{config['color']}"
            }
        }), text = True)

        # Handle our screen
        screen_task = asyncio.create_task(screen.process_task())

        # Stop this dumbass thread from exiting
        while True:
            try:
                message = orjson.loads(await websocket.recv())
                screen.queue_event(ScreenEvent("message", MessageEvent(MessageAuthor("Internal", "ffffff"), str(message))))
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
