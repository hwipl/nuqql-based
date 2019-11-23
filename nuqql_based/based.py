#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from nuqql_based.account import load_accounts
from nuqql_based.logger import init_main_logger, init_account_loggers
from nuqql_based.config import init_config
from nuqql_based.server import run_server


def main():
    """
    Main function
    """

    # initialize configuration from command line and config file
    config = init_config()

    # initialize main logger
    init_main_logger(config)

    # load accounts
    accounts = load_accounts()

    # initialize account loggers
    init_account_loggers(config, accounts)

    # start server
    try:
        run_server(config)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
