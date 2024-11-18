# Copyright (c) 2024 iiPython

import sys
from readchar import readkey, key

def show_menu(options: list[str]) -> str:
    iterated, length, index = 0, len(options), 0
    while True:
        sys.stdout.write(f"\033[{length}F" * iterated)

        # Handle control
        if iterated:
            match readkey():
                case key.UP | "w":
                    index = length - 1 if index - 1 < 0 else index - 1

                case key.DOWN | "s":
                    index = 0 if index + 1 >= length else index + 1

                case key.ENTER:
                    sys.stdout.write("\n" * length)
                    sys.stdout.flush()
                    return options[index]

                case key.CTRL_C:
                    raise KeyboardInterrupt

        # Print out options
        for i, option in enumerate(options):
            index_text = f"\033[32m{i + 1}\033[0m"
            if i == index:
                option_text = f"\033[33m{option}\033[0m"
                suffix_text = "\033[2m<--\033[22m"

            else:
                option_text, suffix_text = option, ""

            index_text = f"  {index_text}"
            sys.stdout.write(f"\033[2K{index_text}\t{option_text} {suffix_text}\n")

        iterated = 1
