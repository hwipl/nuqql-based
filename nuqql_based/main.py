#!/usr/bin/env python3

"""
Basic nuqql backend main entry point
"""

import asyncio
import time

from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Tuple

from nuqql_based.based import Based
from nuqql_based.buddy import Buddy
from nuqql_based.callback import Callback
from nuqql_based.message import Message

if TYPE_CHECKING:   # imports for typing
    from nuqql_based.account import Account     # noqa

CallbackFunc = Callable[[Optional["Account"], Callback, Tuple], Awaitable[str]]

VERSION = "0.2.0"

# buddy list for testing only; only supports one account
TEST_BUDDIES: List[Buddy] = []


async def set_status(acc: Optional["Account"], _cmd: Callback,
                     params: Tuple) -> str:
    """
    Set the status of the account
    """

    assert acc
    status = params[0]
    acc.status = status
    acc.receive_msg(Message.status(acc, status))
    return ""


async def get_status(acc: Optional["Account"], _cmd: Callback,
                     _params: Tuple) -> str:
    """
    Get the status of the account
    """

    assert acc
    acc.receive_msg(Message.status(acc, acc.status))
    return ""


def _add_buddy(name: str) -> None:
    """
    Add a buddy to the testing buddy list
    """

    for buddy in TEST_BUDDIES:
        if buddy.name == name:
            return

    # new buddy
    buddy = Buddy(name, "", "")
    TEST_BUDDIES.append(buddy)


async def send_message(acc: Optional["Account"], _cmd: Callback,
                       params: Tuple) -> str:
    """
    Send a message to another user. For testing, this simply modifies the
    message and returns it to the sender.
    """

    assert acc
    dest, msg = params

    # add destination as buddy in the testing buddy list
    _add_buddy(dest)

    acc.receive_msg(Message.message(acc, str(int(time.time())), dest, acc.user,
                                    msg.upper()))
    return ""


async def _update_buddies(acc: Optional["Account"], _cmd: Callback,
                          params: Tuple) -> str:
    """
    Get buddy list. For testing, this simply returns a single buddy list for
    all accounts.
    """

    # filter online users?
    online = False
    if params:
        online = params[0]

    # construct buddy messages
    assert acc
    result = ""
    for buddy in TEST_BUDDIES:
        if online and buddy.status != "Available":
            continue
        result += Message.buddy(acc, buddy)

    return result


async def _main() -> None:
    """
    Main function
    """

    based = Based("based", VERSION)
    callbacks: List[Tuple[Callback, CallbackFunc]] = [
        (Callback.SET_STATUS, set_status),
        (Callback.GET_STATUS, get_status),
        (Callback.SEND_MESSAGE, send_message),
        (Callback.UPDATE_BUDDIES, _update_buddies),
    ]
    based.set_callbacks(callbacks)
    await based.start()


def main() -> None:
    """
    Main entry point
    """

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
