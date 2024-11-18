# Copyright (c) 2024 iiPython

# Modules
import asyncio
from typing import Callable

import orjson
from websockets import connect

from .types import User, Message

# Context
class Context:
    def __init__(self, socket, message: Message) -> None:
        self.socket, self.message = socket, message

    async def send(self, message: str) -> None:
        await self.socket.send(orjson.dumps({"type": "message", "data": {"text": message}}), text = True)

    async def reply(self, message: str) -> None:
        await self.send(f"[Reply to {self.message.user.name}] {message}")

# Main client class
class Client:
    def __init__(self) -> None:
        self._connected: Callable | None = None
        self._on_message: Callable | None = None

    # Handle user data
    def setup_profile(self, username: str, color: str) -> None:
        """Initialize the user profile with the given username and color."""
        self.user = {"name": f"[BOT] {username}", "color": color}

    # Main event loop
    async def _loop(self) -> None:
        while self.socket:
            payload = orjson.loads(await self.socket.recv())
            data = payload.get("data", {})

            # Handle all the different types
            match payload["type"]:
                case "message":
                    if data.get("history") is True:
                        continue  # Ignore history messages

                    if self._on_message is not None:
                        message = Message(
                            User(*data["user"].values()),
                            data["text"]
                        )
                        await self._on_message(
                            Context(self.socket, message),
                            message
                        )

    async def send(self, type: str, **data) -> None:
        """Send the given type and payload to the server."""
        await self.socket.send(orjson.dumps({"type": type, "data": data}), text = True)

    async def connect(self, address: str) -> None:
        """Connect to the given Nightwatch server and begin handling messages."""

        # Check if we're missing user information
        if not hasattr(self, "user"):
            raise ValueError("No user information has been provided yet!")

        # Parse the address
        address_parts = address.split(":")
        host, port = address_parts[0], 443 if len(address_parts) == 1 else int(address_parts[1])

        # Connect to websocket gateway
        async with connect(f"ws{'s' if port == 443 else ''}://{host}:{port}/gateway") as socket:
            self.socket = socket

            # Handle events
            await self.send("identify", **self.user)
            if self._connected is not None:
                await self._connected()

            await self._loop()

    def run(self, address: str) -> None:
        """Passthrough method to run :client.connect: asynchronously and start the event loop.
        This is the recommended method to use when launching a client."""
        asyncio.run(self.connect(address))

    # Handle event connections
    def connected(self, func: Callable) -> None:
        """Attach a listener to the :connected: event."""
        self._connected = func

    def on_message(self, func: Callable) -> None:
        """Attach a listener to the :on_message: event."""
        self._on_message = func
