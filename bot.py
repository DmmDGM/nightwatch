# Copyright (c) 2024 iiPython

# Modules
import random

from nightwatch.bot import Client
from nightwatch.bot.types import Message

# Initialization
client = Client()
client.setup_profile(username = "iiPythonator", color = "28c1b5")

# Handle events
@client.connected
async def on_connected() -> None:
    print("Bot is connected!")

@client.on_message
async def on_message(ctx, message: Message) -> None:
    if message.text == "fuck you iipythonator":
        return await ctx.run_command("admin", {"command": ["ban", message.user.name]})
    
    if message.text[0] != "!":
        return
    match message.text[1:].split(" "):
        case ["help"]:
            await ctx.reply("Commands: help, fuckyou, dick, nightwatch")
        case ["fuckyou"]:
            await ctx.reply("Fuck you!")
        case ["dick"]:
            await ctx.reply(f"8{'=' * random.randint(4, 14)}D")
        case ["nightwatch"]:
            await ctx.reply("!nightwatch [admin code]")
        case ["nightwatch", code]:
            result = (await ctx.run_command("admin", {"code": code}))["data"]
            if result.get("sucess") is not True:
                return await ctx.reply("Invalid admin code, lmao!")
    
            await ctx.run_command("admin", {"command": ["say", "This is a test message."]})

# Launch bot
client.run(address = "nightwatch.k4ffu.dev")