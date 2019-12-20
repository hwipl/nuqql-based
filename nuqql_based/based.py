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

    def __init__(self, name: str, version: str) -> None:
        # callbacks
        self.callbacks = Callbacks()

        # config
        self.config = Config(name, version)

        # loggers
        self.loggers = Loggers(self.config)

        # account list
        self.accounts = AccountList(self.config, self.loggers, self.callbacks)

        # server
        self.server = Server(self.config, self.loggers, self.callbacks,
                             self.accounts)

    def set_callbacks(self, callbacks: CallbackList) -> None:
        """
        Set callbacks of the backend to the (callback, function) tuple values
        in the callbacks list
        """

        # register all callbacks
        for cback, func in callbacks:
            self.callbacks.add(cback, func)

    def start(self) -> None:
        """
        Start based
        """

        # load config from command line arguments and config file
        self.config.init()
        self.callbacks.call(Callback.BASED_CONFIG, -1, (self.config, ))

        # init main logger
        self.loggers.init_main()

        # load account list
        self.accounts.load()

        # start server
        try:
            self.server.run()
        except KeyboardInterrupt:
            self.callbacks.call(Callback.BASED_INTERRUPT, -1, ())
        finally:
            self.callbacks.call(Callback.BASED_QUIT, -1, ())
            sys.exit()
