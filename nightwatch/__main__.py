# Copyright (c) 2024 iiPython

from nightwatch.config import config

# Initialization
def main() -> None:
    from argparse import ArgumentParser
    from nightwatch.client import start_client

    # Handle CLI options
    ap = ArgumentParser(
        prog = "nightwatch",
        description = "The chatting application to end all chatting applications.\nhttps://github.com/iiPythonx/nightwatch",
        epilog = "Copyright (c) 2024 iiPython"
    )
    ap.add_argument("-a", "--address", help = "the nightwatch server to connect to")
    ap.add_argument("-u", "--username", help = "the username to use")
    ap.add_argument("-r", "--reset", action = "store_true", help = "reset the configuration file")

    # Launch client
    args = ap.parse_args()
    if args.reset:
        config.reset()

    start_client(args.address, args.username)
