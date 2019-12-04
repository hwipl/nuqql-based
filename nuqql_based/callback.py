"""
Nuqql-based callbacks
"""

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


class Callbacks:
    """
    Callbacks class
    """

    def __init__(self):
        self.callbacks = {}

    def add(self, name, func):
        """
        Register a callback
        """
        self.callbacks[name] = func

    def delete(self, name):
        """
        Unregister a callback
        """

        if name in self.callbacks:
            del self.callbacks[name]

    def call(self, name, account_id, params):
        """
        Call callback if it is registered
        """

        if name in self.callbacks:
            return self.callbacks[name](account_id, name, params)

        return ""
