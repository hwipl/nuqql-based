#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from nuqql_based.callback import Callback
from nuqql_based import account
from nuqql_based import config
from nuqql_based import logger
from nuqql_based import server


def start(name, callbacks):
    """
    Initialize and start based with name and list of callbacks
    """

    # register all callbacks
    for cback, func in callbacks:
        cback.register(func)

    # initialize configuration from command line and config file
    conf = config.init_config(name)
    Callback.BASED_CONFIG.call(-1, (conf, ))

    # initialize main logger
    logger.init_main_logger(conf)

    # load accounts
    accounts = account.load_accounts()

    # initialize account loggers
    logger.init_account_loggers(conf, accounts)

    # call add account callback for each account
    for acc in accounts.values():
        Callback.ADD_ACCOUNT.call(acc.aid, (acc, ))

    # start server
    try:
        server.run_server(conf)
    except KeyboardInterrupt:
        Callback.BASED_INTERRUPT.call(-1, ())
    finally:
        Callback.BASED_QUIT.call(-1, ())
        sys.exit()


def main():
    """
    Main function
    """

    start("based", [])


if __name__ == "__main__":
    main()
