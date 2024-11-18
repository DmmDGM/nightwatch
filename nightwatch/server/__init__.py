# Copyright (c) 2024 iiPython

# Modules
import orjson
from pydantic import ValidationError
from websockets import WebSocketCommonProtocol
from websockets.exceptions import ConnectionClosed

from .utils.commands import registry, broadcast, Constant
from .utils.websocket import NightwatchClient
from .utils.modules.admin import admin_module

from nightwatch.logging import log

# Handle state
class NightwatchStateManager():
    def __init__(self) -> None:
        self.clients = {}
        self.chat_history = []

    def add_client(self, client: WebSocketCommonProtocol) -> None:
        self.clients[client] = None
        setattr(client, "ip", client.request.headers.get("CF-Connecting-IP", client.remote_address[0]))

    def remove_client(self, client: WebSocketCommonProtocol) -> None:
        if client in self.clients:
            del self.clients[client]

state = NightwatchStateManager()

# Socket entrypoint
async def connection(websocket: WebSocketCommonProtocol) -> None:
    client = NightwatchClient(state, websocket)
    if websocket.ip in admin_module.banned_users:  # type: ignore
        return await client.send("error", text = "You have been banned from this server.")

    try:
        log.info(client.id, "Client connected!")

        async for message in websocket:
            message = orjson.loads(message)
            if not isinstance(message, dict):
                await client.send("error", text = "Expected payload is an object.")
                continue

            if message.get("type") not in registry.commands:
                await client.send("error", text = "Specified command type does not exist or is missing.")
                continue

            callback = message.get("callback")
            if callback is not None:
                client.set_callback(callback)

            command, payload_type = registry.commands[message["type"]]
            if payload_type is None:
                await command(state, client)

            else:
                try:
                    await command(state, client, payload_type(**(message.get("data") or {})))

                except ValidationError as error:
                    await client.send("error", text = str(error))

    except orjson.JSONDecodeError:
        log.warn(client.id, "Failed to decode JSON from client.")

    except ConnectionClosed:
        log.info(client.id, "Client disconnected!")
        if client.identified:
            broadcast(state, "message", text = f"{client.user_data['name']} left the chatroom.", user = Constant.SERVER_USER)
            
    state.remove_client(websocket)
