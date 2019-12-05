#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import sys

from typing import Callable, Tuple, List

from nuqql_based.account import AccountList
from nuqql_based.callback import Callbacks, Callback
from nuqql_based.logger import Loggers
from nuqql_based.config import Config
from nuqql_based.server import Server

CallbackFunc = Callable[[int, Callback, Tuple], str]
CallbackTuple = Tuple[Callback, CallbackFunc]
CallbackList = List[CallbackTuple]


class Based:
    """
    Based class
    """

    def __init__(self, name: str, callbacks: CallbackList) -> None:
        # register all callbacks
        self.callbacks = Callbacks()
        for cback, func in callbacks:
            self.callbacks.add(cback, func)

        # load config
        self.config = Config(name)
        self.callbacks.call(Callback.BASED_CONFIG, -1, (self.config.get(), ))

        # init loggers
        self.loggers = Loggers(self.config)

        # init account list
        self.accounts = AccountList(self.config, self.loggers, self.callbacks)
        self.accounts.load()

        # init server
        self.server = Server(self.config, self.loggers, self.callbacks,
                             self.accounts)

    def start(self) -> None:
        """
        Start based
        """

        # start server
        try:
            self.server.run()
        except KeyboardInterrupt:
            self.callbacks.call(Callback.BASED_INTERRUPT, -1, ())
        finally:
            self.callbacks.call(Callback.BASED_QUIT, -1, ())
            sys.exit()


def main() -> None:
    """
    Main function
    """

    based = Based("based", [])
    based.start()


if __name__ == "__main__":
    main()
