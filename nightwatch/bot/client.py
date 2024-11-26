# Copyright (c) 2024 iiPython

# Modules
import typing
import asyncio

import orjson
import requests
from websockets import connect
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed

from .types import from_dict, User, Message, RicsInfo

# Exceptions
class AuthorizationFailed(Exception):
    def __init__(self, message: str, json: dict | None = None) -> None:
        super().__init__(message)
        self.json = json

class Disconnected(Exception):
    pass

# Handle state
class ClientState:
    """The current client state. Includes data such as the user list, chat logs, and websocket connection."""
    def __init__(self) -> None:
        self.user_list: list[User]
        self.chat_logs: list[Message]
        self.rics_info: dict[str, str]
        self.socket   : ClientConnection

class Context:
    """An object to store data about the current event context."""
    def __init__(
        self,
        state: ClientState,
        message: typing.Optional[Message] = None,
        user: typing.Optional[User] = None
    ) -> None:
        self.state = state
        self.rics = RicsInfo(
            name = state.rics_info["name"],
            users = state.user_list,
            chat_logs = state.chat_logs
        )
        """The RICS (Realtime Info and Communication System) server we are connected to."""

        if message is not None:
            self.message = message
            """The message we just received. This will be None if this is accessed from anything other then :on_message:."""

        if user is not None:
            self.user = user
            """The user who left or joined the server, or the author of the message we just received."""

    async def send(self, message: str) -> None:
        await self.state.socket.send(orjson.dumps({"type": "message", "data": {"message": message}}), text = True)

    async def reply(self, message: str) -> None:
        await self.send(f"[↑ {self.message.user.name}] {message}")

    def __repr__(self) -> str:
        return f"<Context rics={self.rics} message={getattr(self, 'message', None)} user={getattr(self, 'user', None)}>"

# Main client class
class Client:
    """The main client class, override events on this class and call :run: to start the client."""
    def __init__(self) -> None:
        self.__state = ClientState()
        self.__session = requests.Session()

        # Public attributes (provided just for the hell of it)
        self.user: User | None = None
        """The current user this client is connected as."""
        self.address: str | None = None
        """The address this client is connected to."""

    # Events (for overwriting)
    async def on_connect(self, ctx: Context) -> None:
        """Listen to the :connect: event."""
        pass

    async def on_message(self, ctx: Context) -> None:
        """Listen to the :message: event."""
        pass

    async def on_join(self, ctx: Context) -> None:
        """Listen to the :join: event."""
        pass

    async def on_leave(self, ctx: Context) -> None:
        """Listen to the :leave: event."""
        pass

    # Handle running
    async def __authorize(self, username: str, hex: str, address: str) -> tuple[str, int, str, str]:
        """Given an authorization payload, attempt an authorization request.
        
        Return:
          :host:     (str) -- hostname of the backend
          :port:     (int) -- port of the backend
          :protocol: (str) -- ws(s):// depending on the port
          :auth:     (str) -- authorization code"""
        host, port = (address if ":" in address else f"{address}:443").split(":")
        protocol = "s" if port == "443" else ""

        # Establish authorization
        try:
            response = self.__session.post(
                f"http{protocol}://{host}:{port}/api/join",
                json = {"username": username, "hex": hex, "bot": True},
                timeout = 5
            )
            response.raise_for_status()

            # Handle payload
            payload = response.json()
            if payload["code"] != 200:
                raise AuthorizationFailed("Connection failed!", payload)

            return host, int(port), f"ws{protocol}://", payload["authorization"]

        except requests.RequestException as e:
            raise AuthorizationFailed("Connection failed!", e.response.json() if e.response is not None else None)

    async def __match_event(self, event: dict[str, typing.Any]) -> None:
        match event:
            case {"type": "rics-info", "data": payload}:
                self.__state.chat_logs = [from_dict(Message, message) for message in payload["message-log"]]
                self.__state.user_list = [from_dict(User, user) for user in payload["user-list"]]
                self.__state.rics_info = {"name": payload["name"]}
                await self.on_connect(Context(self.__state))

            case {"type": "message", "data": payload}:
                message = from_dict(Message, payload)

                # Propagate
                await self.on_message(Context(self.__state, message = message, user = message.user))
                self.__state.chat_logs.append(message)

            case {"type": "join", "data": payload}:
                user = from_dict(User, payload["user"])
                if user == self.user:
                    return

                self.__state.user_list.append(user)
                await self.on_join(Context(self.__state, user = user))

            case {"type": "leave", "data": payload}:
                user = from_dict(User, payload["user"])
                self.__state.user_list.remove(user)
                await self.on_leave(Context(self.__state, user = user))

    async def event_loop(self, username: str, hex: str, address: str) -> None:
        """Establish a connection and listen to websocket messages.
        This method shouldn't be called directly, use :Client.run: instead."""

        host, port, protocol, auth = await self.__authorize(username, hex, address)
        self.user, self.address = User(username, hex, False, True), address

        try:
            async with connect(f"{protocol}{host}:{port}/api/ws?authorization={auth}") as socket:
                self.__state.socket = socket
                while socket.state == 1:
                    await self.__match_event(orjson.loads(await socket.recv()))

        except ConnectionClosed:
            raise Disconnected("RICS socket has been disconnected!")

    async def close(self) -> None:
        """Closes the websocket connection."""
        await self.__state.socket.close()

    def run(
        self,
        username: str,
        hex: str,
        address: str
    ):
        """Start the client and run the event loop.

        Arguments:
          :username: (str) -- the username to connect with
          :hex:      (str) -- the hex color code to connect with
          :address:  (str) -- the FQDN to connect to
        """
        asyncio.run(self.event_loop(username, hex, address))
