# Copyright (c) 2024 iiPython

# Modules
from nightwatch.bot import Client

# Create client
class NextgenerationBot(Client):
    def __init__(self) -> None:
        super().__init__()

    # Handle events
    # async def on_message(self, ctx) -> None:
        # print(f"Connected to '{ctx.rics.name}' as {self.user.name}!")

NextgenerationBot().run(
    username = "Next-gen Bot",
    hex = "ff0000",
    address = "localhost:8000"
)
