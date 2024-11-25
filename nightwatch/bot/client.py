# Copyright (c) 2024 iiPython

# Modules
import asyncio
from typing import Callable

import orjson
import requests
from websockets import connect

from .types import User, Message, Server

# Context
class Context:
    def __init__(self, socket, message: Message | None, server: Server) -> None:
        self.socket, self.message, self.server = socket, message, server

    async def send(self, message: str) -> None:
        await self.socket.send(orjson.dumps({"type": "message", "data": {"message": message}}), text = True)

    async def reply(self, message: str) -> None:
        if self.message is None:
            raise RuntimeError("Cannot reply to a context with no message information!")

        await self.send(f"[↑ {self.message.user.name}] {message}")

    async def run_command(self, command: str, data: dict) -> dict:
        await self.socket.send(orjson.dumps({"type": command, "data": data}))
        return orjson.loads(await self.socket.recv())

# Main client class
class Client:
    def __init__(self) -> None:
        self.callbacks: dict[str, Callable] = {}

    # Handle user data
    def setup_profile(self, username: str, hex: str) -> None:
        """Initialize the user profile with the given username and hex."""
        self.user = {"username": f"[BOT] {username}", "hex": hex}

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
            self.socket, self.server = socket, None
            while socket:
                match orjson.loads(await socket.recv()):
                    case {"type": "rics-info", "data": {"name": name, "message-log": message_log, "user-list": user_list}}:
                        self.server = Server(url, name, [User(**user) for user in user_list])
                        if "connected" in self.callbacks:
                            await self.callbacks["connected"](Context(socket, None, self.server))

                        if "message-log" in self.callbacks:
                            await self.callbacks["message-log"](
                                Context(socket, None, self.server),
                                [Message.from_payload(message) for message in message_log]
                            )

                    case {"type": "message", "data": payload} if self.server and "message" in self.callbacks:
                        message = Message(**payload)
                        await self.callbacks["message"](Context(socket, message, self.server), message)

                    case {"type": "join", "data": {"user": user, "time": _}} if self.server and "join" in self.callbacks:
                        await self.callbacks["join"](Context(socket, None, self.server), User.from_payload(user))

                    case {"type": "leave", "data": {"user": user, "time": _}} if self.server and "leave" in self.callbacks:
                        await self.callbacks["leave"](Context(socket, None, self.server), User.from_payload(user))

    def run(self, address: str) -> None:
        """Passthrough method to run :client.connect: asynchronously and start the event loop.
        This is the recommended method to use when launching a client."""
        asyncio.run(self.connect(address))

    # Handle event connections
    def event(self, event_name: str) -> Callable:
        """Attach a listener to a specific Nightwatch event."""
        def internal_callback(func: Callable) -> None:
            self.callbacks[event_name] = func

        return internal_callback
