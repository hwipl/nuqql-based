#!/usr/bin/env python3

"""
Basic nuqql backend main entry point
"""

import time

from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from nuqql_based.based import Based
from nuqql_based.callback import Callback
from nuqql_based.message import Message

if TYPE_CHECKING:   # imports for typing
    from nuqql_based.account import Account     # noqa

CallbackFunc = Callable[[Optional["Account"], Callback, Tuple], str]

VERSION = "0.2.0"


def set_status(acc: Optional["Account"], _cmd: Callback, params: Tuple) -> str:
    """
    Set the status of the account
    """

    assert acc
    status = params[0]
    acc.status = status
    acc.receive_msg(Message.status(acc, status))
    return ""


def get_status(acc: Optional["Account"], _cmd: Callback,
               _params: Tuple) -> str:
    """
    Get the status of the account
    """

    assert acc
    acc.receive_msg(Message.status(acc, acc.status))
    return ""


def send_message(acc: Optional["Account"], _cmd: Callback,
                 params: Tuple) -> str:
    """
    Send a message to another user. For testing, this simply modifies the
    message and returns it to the sender.
    """

    assert acc
    dest, msg = params
    acc.receive_msg(Message.message(acc, str(int(time.time())), dest, acc.user,
                                    msg.upper()))
    return ""


def main() -> None:
    """
    Main function
    """

    based = Based("based", VERSION)
    callbacks: List[Tuple[Callback, CallbackFunc]] = [
        (Callback.SET_STATUS, set_status),
        (Callback.GET_STATUS, get_status),
        (Callback.SEND_MESSAGE, send_message),
    ]
    based.set_callbacks(callbacks)
    based.start()


if __name__ == "__main__":
    main()
