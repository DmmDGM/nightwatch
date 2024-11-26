# Copyright (c) 2024 iiPython

# Modules
from nightwatch.bot import Client, Context

# Create client
class NextgenerationBot(Client):
    async def on_connect(self, ctx: Context) -> None:
        print(f"Connected to '{ctx.rics.name}'!")

    async def on_message(self, ctx: Context) -> None:
        print(f"{ctx.user.name} sent '{ctx.message.message}'")

    async def on_join(self, ctx: Context) -> None:
        print(ctx.rics.name)
        return await ctx.send(f"{ctx.user.name}, why the fuck would you join this place?")

NextgenerationBot().run(
    username = "Next-gen Bot",
    hex = "ff0000",
    address = "nightwatch.k4ffu.dev"
)
