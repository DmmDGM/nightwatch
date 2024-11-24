# Copyright (c) 2024 iiPython

# Modules
import typing
from time import time
from secrets import token_urlsafe

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketDisconnect, WebSocketState

from nightwatch.config import fetch_config

# Load config data
NIGHTWATCH_USER = {"name": "Nightwatch", "hex": "555753"}
config = fetch_config("rics")

# Initialization
app = FastAPI(
    openapi_url = None
)

# Scaffold the application
app.state.clients = {}
app.state.pending_clients = {}
app.state.message_log = []

async def broadcast(payload: dict) -> None:
    payload["data"]["time"] = round(time())
    for client in app.state.clients.values():
        await client.send(payload)

    if payload["type"] == "message":
        app.state.message_log = app.state.message_log[-24:] + [payload["data"]]

app.state.broadcast = broadcast

# Setup routing
class Client:
    def __init__(self, websocket: WebSocket, user_data) -> None:
        self.websocket = websocket
        self.username, self.hex_code = user_data["username"], user_data["hex"]

        # Attach to client list
        self.admin = False
        app.state.clients[self.username] = self

    def serialize(self) -> dict[str, str]:
        return {"name": self.username, "hex": self.hex_code}

    def cleanup(self) -> None:
        del app.state.clients[self.username]
        del self  # Not sure if this helps, in case Python doesn't GC

    async def send(self, payload: dict) -> None:
        if self.websocket.client_state != WebSocketState.CONNECTED:
            return

        try:
            await self.websocket.send_json(payload)

        except WebSocketDisconnect:
            pass

    async def receive(self) -> typing.Any:
        try:
            return await self.websocket.receive_json()

        except WebSocketDisconnect:
            return None

class ClientJoinModel(BaseModel):
    username: str = Field(..., min_length = 3, max_length = 30)
    hex: str = Field(..., min_length = 6, max_length = 6, pattern = "^[0-9A-Fa-f]{6}$")

@app.post("/api/join")
async def route_index(client: ClientJoinModel) -> JSONResponse:
    if client.username in app.state.clients:
        return JSONResponse({
            "code": 400,
            "message": "Requested username is in use on this server."
        }, status_code = 400)

    client_token = token_urlsafe()
    app.state.pending_clients[client_token] = client.model_dump()
    return JSONResponse({
        "code": 200,
        "authorization": client_token
    })

@app.websocket("/api/ws")
async def connect_endpoint(
    authorization: str,
    websocket: WebSocket
) -> None:
    if authorization not in app.state.pending_clients:
        return await websocket.close(1008)

    user_data = app.state.pending_clients[authorization]
    del app.state.pending_clients[authorization]

    await websocket.accept()

    # Initialize client
    client = Client(websocket, user_data)

    # Get the client up to speed
    await client.send({"type": "rics-info", "data": {"name": config["name"] or "Nightwatch Server"}})
    await client.send({"type": "message-log", "data": app.state.message_log})

    # Broadcast join
    await app.state.broadcast({"type": "join", "data": {"user": client.serialize()}})
    await app.state.broadcast({"type": "message", "data": {"user": NIGHTWATCH_USER, "message": f"{client.username} has joined the server."}})

    # Handle loop
    while websocket.client_state == WebSocketState.CONNECTED:
        match await client.receive():
            case {"type": "message", "data": {"message": message}}:
                await app.state.broadcast({"type": "message", "data": {"user": client.serialize(), "message": message}})

            case {"type": "user-list", "data": {"callback": callback}}:
                await client.send({"type": "response", "data": {
                    "user-list": [client.serialize() for client in app.state.clients.values()],
                    "callback": callback
                }})

            case {"type": "admin-list", "data": {"callback": callback}}:
                await client.send({"type": "response", "data": {
                    "admin-list": [client.serialize() for client in app.state.clients.values() if client.admin],
                    "callback": callback
                }})

            case _:
                await client.send({"type": "problem", "data": {"message": "Invalid payload received."}})

    await app.state.broadcast({"type": "leave", "data": {"user": client.serialize()}})
    await app.state.broadcast({"type": "message", "data": {"user": NIGHTWATCH_USER, "message": f"{client.username} has left the server."}})
    client.cleanup()
