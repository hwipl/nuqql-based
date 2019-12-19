"""
Nuqql-based callbacks
"""

from typing import Callable, Dict, Tuple
from enum import Enum


class Callback(Enum):
    """
    CALLBACKS constants
    """

    # based events
    BASED_CONFIG = "BASED_CONFIG"
    BASED_INTERRUPT = "BASED_INTERRUPT"
    BASED_QUIT = "BASED_QUIT"

    # nuqql commands
    QUIT = "QUIT"
    DISCONNECT = "DISCONNECT"
    SEND_MESSAGE = "SEND_MESSAGE"
    GET_MESSAGES = "GET_MESSAGE"
    COLLECT_MESSAGES = "COLLECT_MESSAGES"
    ADD_ACCOUNT = "ADD_ACCOUNT"
    DEL_ACCOUNT = "DEL_ACCOUNT"
    UPDATE_BUDDIES = "UPDATE_BUDDIES"
    GET_STATUS = "GET_STATUS"
    SET_STATUS = "SET_STATUS"
    CHAT_LIST = "CHAT_LIST"
    CHAT_JOIN = "CHAT_JOIN"
    CHAT_PART = "CHAT_PART"
    CHAT_USERS = "CHAT_USERS"
    CHAT_SEND = "CHAT_SEND"
    CHAT_INVITE = "CHAT_INVITE"
    VERSION = "VERSION"


CallbackFunc = Callable[[int, Callback, Tuple], str]


class Callbacks:
    """
    Callbacks class
    """

    def __init__(self) -> None:
        self.callbacks: Dict[Callback, CallbackFunc] = {}

    def add(self, name: Callback, func: CallbackFunc) -> None:
        """
        Register a callback
        """
        self.callbacks[name] = func

    def delete(self, name: Callback) -> None:
        """
        Unregister a callback
        """

        if name in self.callbacks:
            del self.callbacks[name]

    def call(self, name: Callback, account_id: int, params: Tuple) -> str:
        """
        Call callback if it is registered
        """

        if name in self.callbacks:
            return self.callbacks[name](account_id, name, params)

        return ""
