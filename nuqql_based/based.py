"""
Basic nuqql backend
"""

import asyncio

from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Tuple

import nuqql_based.logger

from nuqql_based.account import AccountList
from nuqql_based.callback import Callbacks, Callback
from nuqql_based.config import Config
from nuqql_based.server import Server

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql_based.account import Account  # noqa

CallbackFunc = Callable[[Optional["Account"], Callback, Tuple], Awaitable[str]]
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

        # create a message queue for message exchange between accounts and the
        # based server
        queue: asyncio.Queue = asyncio.Queue()

        # account list
        self.accounts = AccountList(self.config, self.callbacks, queue)

        # server
        self.server = Server(self.config, self.callbacks, self.accounts, queue)

    def set_callbacks(self, callbacks: CallbackList) -> None:
        """
        Set callbacks of the backend to the (callback, function) tuple values
        in the callbacks list
        """

        # register all callbacks
        for cback, func in callbacks:
            self.callbacks.add(cback, func)

    async def start(self) -> None:
        """
        Start based
        """

        # load config from command line arguments and config file
        self.config.init()
        await self.callbacks.call(Callback.BASED_CONFIG, None, (self.config, ))

        # logging
        nuqql_based.logger.init(self.config)

        # load account list
        await self.accounts.load()

        # start server
        try:
            await self.server.run()
        except asyncio.CancelledError:
            await self.callbacks.call(Callback.BASED_INTERRUPT, None, ())
        finally:
            await self.callbacks.call(Callback.BASED_QUIT, None, ())
