#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from nuqql_based.account import AccountList
from nuqql_based.callback import Callback
from nuqql_based.config import Config
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
    config = Config(name)
    conf = config.get()
    Callback.BASED_CONFIG.call(-1, (conf, ))

    # initialize main logger
    logger.init_main_logger(conf)

    # load accounts
    account_list = AccountList(conf)
    accounts = account_list.load()

    # initialize account loggers
    logger.init_account_loggers(conf, accounts)

    # call add account callback for each account
    for acc in accounts.values():
        Callback.ADD_ACCOUNT.call(acc.aid, (acc, ))

    # start server
    try:
        server.run_server(conf, account_list)
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
