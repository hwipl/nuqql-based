#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from nuqql_based.account import AccountList
from nuqql_based.callback import Callbacks, Callback
from nuqql_based.logger import Loggers
from nuqql_based.config import Config
from nuqql_based.server import Server


def start(name, callback_list):
    """
    Initialize and start based with name and list of callbacks
    """

    # register all callbacks
    callbacks = Callbacks()
    for cback, func in callback_list:
        callbacks.add(cback, func)

    # initialize configuration from command line and config file
    config = Config(name)
    conf = config.get()
    callbacks.call(Callback.BASED_CONFIG, -1, (conf, ))

    # initialize main logger
    loggers = Loggers(config)

    # load accounts
    account_list = AccountList(config, loggers, callbacks)
    accounts = account_list.load()


    # start server
    try:
        server = Server(config, loggers, callbacks, account_list)
        server.run()
    except KeyboardInterrupt:
        callbacks.call(Callback.BASED_INTERRUPT, -1, ())
    finally:
        callbacks.call(Callback.BASED_QUIT, -1, ())
        sys.exit()


def main():
    """
    Main function
    """

    start("based", [])


if __name__ == "__main__":
    main()
