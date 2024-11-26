# Copyright (c) 2024 iiPython

# Modules
import typing
import asyncio

import orjson
import requests
from websockets import connect
from websockets.asyncio.client import ClientConnection

from .types import from_dict, User, Message, RicsInfo

# Exceptions
class AuthorizationFailed(Exception):
    pass

# Handle state
class ClientState:
    def __init__(self) -> None:
        self.user_list: list[User]
        self.chat_logs: list[Message]
        self.rics_info: dict[str, str]
        self.socket   : ClientConnection

class Context:
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

        if message is not None:
            self.message = message

        if user is not None:
            self.user = user

    async def send(self, message: str) -> None:
        await self.state.socket.send(orjson.dumps({"type": "message", "data": {"message": message}}), text = True)

    async def reply(self, message: str) -> None:
        await self.send(f"[↑ {self.message.user.name}] {message}")

    def __repr__(self) -> str:
        return f"<Context rics={self.rics} message={getattr(self, 'message', None)} user={getattr(self, 'user', None)}>"

# Main client class
class Client:
    def __init__(self) -> None:
        self.__state = ClientState()
        self.__session = requests.Session()

    # Events (for overwriting)
    async def on_connect(self, _) -> None:
        pass

    async def on_message(self, _) -> None:
        pass

    async def on_join(self, _) -> None:
        pass

    async def on_leave(self, _) -> None:
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
                raise AuthorizationFailed(response)

            return host, int(port), f"ws{protocol}://", payload["authorization"]

        except requests.RequestException:
            raise AuthorizationFailed("Connection failed!")

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
                await self.on_message(Context(self.__state, message))
                self.__state.chat_logs.append(message)

            case {"type": "join", "data": payload}:
                user = from_dict(User, payload["user"])
                self.__state.user_list.append(user)
                await self.on_join(Context(self.__state, user = user))

            case {"type": "leave", "data": payload}:
                user = from_dict(User, payload["user"])
                self.__state.user_list.remove(user)
                await self.on_leave(Context(self.__state, user = user))

    async def __event_loop(self, username: str, hex: str, address: str) -> None:
        """Establish a connection and listen to websocket messages.
        This method shouldn't be called directly, use :Client.run: instead."""

        host, port, protocol, auth = await self.__authorize(username, hex, address)
        async with connect(f"{protocol}{host}:{port}/api/ws?authorization={auth}") as socket:
            self.__state.socket = socket
            while socket.state == 1:
                await self.__match_event(orjson.loads(await socket.recv()))

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
        asyncio.run(self.__event_loop(username, hex, address))
