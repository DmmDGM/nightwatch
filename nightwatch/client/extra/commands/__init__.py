# Copyright (c) 2024 iiPython

# Modules
from typing import Callable

from nightwatch import __version__
from nightwatch.config import config

# Main class
class BaseCommand():
    def __init__(self, name: str, ui, add_message: Callable) -> None:
        self.name, self.ui = name, ui
        self.add_message = add_message

    def print(self, message: str) -> None:
        self.add_message(self.name.title(), message)

# Commands
class ShrugCommand(BaseCommand):
    def __init__(self, *args) -> None:
        super().__init__("shrug", *args)

    def on_execute(self, args: list[str]) -> str:
        return r"¯\_(ツ)_/¯"

class ConfigCommand(BaseCommand):
    def __init__(self, *args) -> None:
        super().__init__("config", *args)

    def on_execute(self, args: list[str]) -> None:
        if not args:
            for line in [
                "Nightwatch client configuration",
                "Usage: /config <key> <value>",
                "",
                "Example usage:",
                "  /config colors.time yellow",
                "  /config prompt \">> \"",
                "  /config client.time_format 24h",
                "",
                "Some changes will only apply after Nightwatch restarts."
            ]:
                self.print(line)

            return

        elif len(args) < 2:
            return self.print(f"Missing the value to assign to '{args[0]}'.")

        config.set(args[0], args[1])
        self.print(f"{args[0]} has been set to \"{args[1]}\".")

class HelpCommand(BaseCommand):
    def __init__(self, *args) -> None:
        super().__init__("help", *args)

    def on_execute(self, args: list[str]) -> None:
        self.print(f"✨ Nightwatch v{__version__}")
        self.print("Available commands:")
        for command in self.ui.commands:
            self.print(f"  /{command}")

class MembersCommand(BaseCommand):
    def __init__(self, *args) -> None:
        super().__init__("members", *args)

    def on_execute(self, args: list[str]) -> None:
        def members_callback(response: dict):
            self.print(", ".join(response["data"]["list"]))

        self.ui.websocket.callback({"type": "members"}, members_callback)

class AdminCommand(BaseCommand):
    def __init__(self, *args) -> None:
        self.admin = False
        super().__init__("admin", *args)

    def on_execute(self, args: list[str]) -> None:
        match args:
            case [] if not self.admin:
                self.ui.websocket.send({"type": "admin"})
                self.print("Run /admin <code> with the admin code in your server console.")

            case [] | ["help"]:
                self.print("Available commands:")
                if not self.admin:
                    self.print("  /admin <admin code>")

                self.print("  /admin ban <username>")
                self.print("  /admin unban <username>")
                self.print("  /admin ip <username>")
                self.print("  /admin banlist")
                self.print("  /admin say <message>")

            case ["ban", username]:
                def on_ban_response(response: dict):
                    if not response["data"]["success"]:
                        return self.print(f"(fail) {response['data']['error']}")

                    self.print(f"(success) {username} has been banned.")

                self.ui.websocket.callback({"type": "admin", "data": {"command": args}}, on_ban_response)

            case ["unban", username]:
                def on_unban_response(response: dict):
                    if not response["data"]["success"]:
                        return self.print(f"(fail) {response['data']['error']}")

                    self.print(f"(success) {username} has been unbanned.")

                self.ui.websocket.callback({"type": "admin", "data": {"command": args}}, on_unban_response)

            case ["ip", username]:
                def on_ip_response(response: dict):
                    if not response["data"]["success"]:
                        return self.print(f"(fail) {response['data']['error']}")

                    self.print(f"(success) {username}'s IP address is {response['data']['ip']}.")

                self.ui.websocket.callback({"type": "admin", "data": {"command": args}}, on_ip_response)

            case ["banlist"]:
                def on_banlist_response(response: dict):
                    if not response["data"]["banlist"]:
                        return self.print("(fail) Nobody is banned on this server.")

                    self.print("Current banlist:")
                    self.print(f"{', '.join(f'{v} ({k})' for k, v in response['data']['banlist'].items())}")

                self.ui.websocket.callback({"type": "admin", "data": {"command": args}}, on_banlist_response)

            case ["say", _]:
                self.ui.websocket.send({"type": "admin", "data": {"command": args}})

            case [code]:
                if self.admin:
                    return self.print("(fail) Privileges already escalated.")

                def on_admin_response(response: dict):
                    if response["data"]["success"] is False:
                        return self.print("(fail) Invalid admin code specified.")

                    self.print("(success) Privileges escalated.")
                    self.admin = True

                self.ui.websocket.callback({"type": "admin", "data": {"code": code}}, on_admin_response)

            case _:
                self.print("Admin command not recognized, try /admin help.")

commands = [
    ShrugCommand,
    ConfigCommand,
    HelpCommand,
    MembersCommand,
    AdminCommand
]
