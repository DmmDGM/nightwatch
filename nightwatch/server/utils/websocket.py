# Copyright (c) 2024 iiPython

# Modules
import random
from typing import Any

import orjson
from websockets import WebSocketCommonProtocol

CLIENT_ID_CHARSET = "abcdefg1234567890"

class NightwatchClient():
    """This class acts as a wrapper on top of WebSocketCommonProtocol that implements
    data serialization through orjson."""
    def __init__(self, state, client: WebSocketCommonProtocol) -> None:
        self.client = client
        self.admin, self.identified, self.callback = False, False, None

        self.state = state
        self.state.add_client(client)

        self.id = "".join(random.choice(CLIENT_ID_CHARSET) for _ in range(6))

    async def send(self, message_type: str, **message_data) -> None:
        payload = {"type": message_type, "data": message_data}
        if self.callback is not None:
            payload["callback"] = self.callback
            self.callback = None

        await self.client.send(orjson.dumps(payload).decode())

    def set_callback(self, callback: str) -> None:
        self.callback = callback

    # Handle user data (ie. name and color)
    def set_user_data(self, data: dict[str, Any]) -> None:
        self.user_data = data
        self.state.clients[self.client] = data["name"]
