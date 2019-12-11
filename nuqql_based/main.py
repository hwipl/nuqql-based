#!/usr/bin/env python3

"""
Basic nuqql backend main entry point
"""

from nuqql_based.based import Based


def main() -> None:
    """
    Main function
    """

    based = Based("based", [])
    based.start()


if __name__ == "__main__":
    main()
