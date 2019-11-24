#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from nuqql_based import callback
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
        callback.register_callback(cback, func)

    # initialize configuration from command line and config file
    conf = config.init_config(name)
    callback.callback(-1, callback.Callback.BASED_CONFIG, (conf, ))

    # initialize main logger
    logger.init_main_logger(conf)

    # load accounts
    accounts = account.load_accounts()

    # initialize account loggers
    logger.init_account_loggers(conf, accounts)

    # call add account callback for each account
    for acc in accounts.values():
        callback.callback(acc.aid, callback.Callback.ADD_ACCOUNT, (acc, ))

    # start server
    try:
        server.run_server(conf)
    except KeyboardInterrupt:
        callback.callback(-1, callback.Callback.BASED_INTERRUPT, ())
    finally:
        callback.callback(-1, callback.Callback.BASED_QUIT, ())
        sys.exit()


def main():
    """
    Main function
    """

    start("based", [])


if __name__ == "__main__":
    main()
