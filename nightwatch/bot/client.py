# Copyright (c) 2024 iiPython

# Modules
import asyncio
from typing import Callable

import orjson
import requests
from websockets import connect

from .types import User, Message

# Context
class Context:
    def __init__(self, socket, message: Message) -> None:
        self.socket, self.message = socket, message

    async def send(self, message: str) -> None:
        await self.socket.send(orjson.dumps({"type": "message", "data": {"message": message}}), text = True)

    async def reply(self, message: str) -> None:
        await self.send(f"[↑ {self.message.user.name}] {message}")

    async def run_command(self, command: str, data: dict) -> dict:
        await self.socket.send(orjson.dumps({"type": command, "data": data}))
        return orjson.loads(await self.socket.recv())

# Main client class
class Client:
    def __init__(self) -> None:
        self._connected: Callable | None = None
        self._on_message: Callable | None = None

    # Handle user data
    def setup_profile(self, username: str, hex: str) -> None:
        """Initialize the user profile with the given username and hex."""
        self.user = {"username": f"[BOT] {username}", "hex": hex}

    # Main event loop
    async def _loop(self) -> None:
        while self.socket:
            payload = orjson.loads(await self.socket.recv())
            data = payload.get("data", {})

            # Handle all the different types
            match payload["type"]:
                case "message":
                    if self._on_message is not None:
                        message = Message(
                            User(*data["user"].values()),
                            data["message"]
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

        # Send authorization request
        protocol, url = "s" if port == 443 else "", f"{host}:{port}"
        authorization = requests.post(f"http{protocol}://{url}/api/join", json = self.user).json()["authorization"]

        # Connect to websocket gateway
        async with connect(f"ws{protocol}://{url}/api/ws?authorization={authorization}") as socket:
            self.socket = socket

            # Handle events
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
