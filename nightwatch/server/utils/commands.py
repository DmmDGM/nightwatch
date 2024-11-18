# Copyright (c) 2024 iiPython

# Modules
import random
from typing import Callable

import orjson
import websockets

from . import models
from .websocket import NightwatchClient
from .modules.admin import admin_module

from nightwatch.logging import log
from nightwatch.config import config

# Constants
class Constant:
    SERVER_USER: dict[str, str] = {"name": "Nightwatch", "color": "gray"}
    SERVER_NAME: str = config["server.name"] or "Untitled Server"
    ADMIN_CODE: str = str(random.randint(100000, 999999))

# Handle command registration
class CommandRegistry():
    def __init__(self) -> None:
        self.commands = {}

    def command(self, name: str) -> Callable:
        def callback(function: Callable) -> None:
            self.commands[name] = (
                function,
                function.__annotations__["data"] if "data" in function.__annotations__ else None
            )

        return callback

registry = CommandRegistry()

# Handle broadcasting
def broadcast(state, type: str, **data) -> None:
    websockets.broadcast(state.clients, orjson.dumps({
        "type": type,
        "data": data
    }).decode())
    if type == "message":
        state.chat_history.append(data)

# Setup commands
@registry.command("identify")
async def command_identify(state, client: NightwatchClient, data: models.IdentifyModel) -> None:
    if client.identified:
        return await client.send("error", text = "You have already identified.")

    elif data.name.lower() in ["nightwatch", "admin", "administrator", "moderator"]:
        return await client.send("error", text = "The specified username is reserved.")

    elif data.name in state.clients.values():
        return await client.send("error", text = "Specified username is already taken.")

    client.set_user_data(data.model_dump())
    client.identified = True

    log.info(client.id, f"Client has identified as '{data.name}'.")

    await client.send("server", name = Constant.SERVER_NAME, online = len(state.clients))
    broadcast(state, "message", text = f"{data.name} joined the chatroom.", user = Constant.SERVER_USER)

    # Send the chat history
    for message in state.chat_history:
        await client.send("message", **message)

@registry.command("message")
async def command_message(state, client: NightwatchClient, data: models.MessageModel) -> None:
    if not client.identified:
        return await client.send("error", text = "You must identify before sending a message.")

    broadcast(state, "message", text = data.text, user = client.user_data)

@registry.command("members")
async def command_members(state, client: NightwatchClient) -> None:
    return await client.send("members", list = list(state.clients.values()))

@registry.command("ping")
async def command_ping(state, client: NightwatchClient) -> None:
    return await client.send("pong")

# New commands (coming back to this branch)
@registry.command("admin")
async def command_admin(state, client: NightwatchClient, data: models.AdminModel) -> None:
    if not client.identified:
        return await client.send("error", text = "You cannot enter admin mode while anonymous.")

    # Handle admin commands
    if client.admin:
        match data.command:
            case ["ban", username]:
                for client_object, client_username in state.clients.items():
                    if client_username == username:
                        await client_object.send(orjson.dumps({
                            "type": "message",
                            "data": {"text": "You have been banned from this server.", "user": Constant.SERVER_USER}
                        }).decode())
                        await client_object.close()
                        admin_module.add_ban(client_object.ip, username)
                        broadcast(state, "message", text = f"{username} has been banned by {client.user_data['name']}.", user = Constant.SERVER_USER)
                        return await client.send("admin", success = True)

                await client.send("admin", success = False, error = "Specified username couldn't be found.")

            case ["unban", username]:
                for ip, client_username in admin_module.banned_users.items():
                    if client_username == username:
                        admin_module.unban(ip)
                        return await client.send("admin", success = True)

                await client.send("admin", success = False, error = "Specified banned user couldn't be found.")

            case ["ip", username]:
                for client_object, client_username in state.clients.items():
                    if client_username == username:
                        return await client.send("admin", success = True, ip = client_object.ip)

                await client.send("admin", success = False, error = "Specified username couldn't be found.")

            case ["banlist"]:
                await client.send("admin", banlist = admin_module.banned_users)

            case ["say", message]:
                broadcast(state, "message", text = message, user = Constant.SERVER_USER)

            case _:
                await client.send("error", text = "Invalid admin command sent, your client might be outdated.")

        return

    # Handle becoming admin
    if data.code is None:
        return log.info("admin", f"Admin code is {Constant.ADMIN_CODE}")

    if data.code != Constant.ADMIN_CODE:
        return await client.send("admin", success = False)

    client.admin = True
    log.info("admin", f"{client.user_data['name']} ({client.id}) is now an administrator.")
    return await client.send("admin", success = True)
