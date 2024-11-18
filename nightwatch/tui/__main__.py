# Copyright (c) 2024 iiPython

# Modules
import re
import asyncio

from nightwatch import __version__, HEX_COLOR_REGEX
from nightwatch.tui import config

from nightwatch.tui.modules.selection import show_menu
from nightwatch.tui.modules.connection import establish_connection

# Initialization
if __name__ == "__main__":
    print(f"\033[H\033[2J✨ \033[32mNightwatch TUI | v{__version__}\033[0m\n")

    # Check username
    username, color = config["username"], config["color"]
    if username is None:
        print("Hi, welcome to Nightwatch! To begin, please come up with a username.")
        print("This can be changed later at any time by running \033[31mnightwatch --reset\033[0m.\n")

        # Handle name validation
        while True:
            username = input("Name > ")
            if username.strip() and len(username) in range(3, 32):
                break

            print("\033[1A\033[0J", end = "")

        config.set("username", username)
        print("\033[4A\033[0J", end = "")  # Reset back up to the Nightwatch label

    # Check color
    if not re.match(HEX_COLOR_REGEX, color or ""):
        while True:
            print("For fun, you can select a color for your username.")
            print("Please enter the HEX code (6 long) you would like to have as your color.")
            color = (input("> #") or "ffffff").lstrip("#")

            # Validate their color choice
            if re.match(HEX_COLOR_REGEX, color):
                break

            print("\033[3A\033[0J", end = "")

        print("\033[3A\033[0J", end = "")
        config.set("color", color)

    # Handle server selection
    servers = config["servers"]
    if servers is None:
        servers = [
            "nightwatch.iipython.dev",
            "nightwatch.k4ffu.dev"
        ]
        config.set("servers", servers)

    print("\033[2mPlease, pick a server to connect to:\033[22m")
    selected_server = show_menu(servers)

    # Parse server address
    host, port = None, None
    match selected_server.split(":"):
        case [host, port]:
            host, port = host, int(port)

        case [host]:
            host, port = host, 443

    print(f"\nConnecting to \033[4m\033[36m{host}:{port}\033[0m ...")
    asyncio.run(establish_connection(host, port))
