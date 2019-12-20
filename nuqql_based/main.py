#!/usr/bin/env python3

"""
Basic nuqql backend main entry point
"""

from nuqql_based.based import Based

VERSION = "0.1"


def main() -> None:
    """
    Main function
    """

    based = Based("based", VERSION)
    based.start()


if __name__ == "__main__":
    main()
