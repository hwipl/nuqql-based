"""
Nuqql-based callbacks
"""

from enum import Enum, auto


class Callback(Enum):
    """
    CALLBACKS constants
    """

    # based events
    BASED_CONFIG = auto()
    BASED_INTERRUPT = auto()
    BASED_QUIT = auto()

    # nuqql commands
    QUIT = auto()
    DISCONNECT = auto()
    SEND_MESSAGE = auto()
    GET_MESSAGES = auto()
    COLLECT_MESSAGES = auto()
    ADD_ACCOUNT = auto()
    DEL_ACCOUNT = auto()
    UPDATE_BUDDIES = auto()
    GET_STATUS = auto()
    SET_STATUS = auto()
    CHAT_LIST = auto()
    CHAT_JOIN = auto()
    CHAT_PART = auto()
    CHAT_USERS = auto()
    CHAT_SEND = auto()
    CHAT_INVITE = auto()

    @staticmethod
    def parse(name):
        """
        Map callback name to callback
        """

        return _CALLBACK_MAP[name]

    def register(self, cb_func):
        """
        Register a callback
        """

        _CALLBACKS[self] = cb_func

    def unregister_callback(self):
        """
        Unregister a callback
        """

        if self in _CALLBACKS:
            del _CALLBACKS[self]

    def call(self, account_id, params):
        """
        Call callback if it is registered
        """

        if self in _CALLBACKS:
            return _CALLBACKS[self](account_id, self, params)

        return ""


# dictionary containing configured callbacks
_CALLBACKS = {}

# map callback names to their enum
_CALLBACK_MAP = {
    # based events
    "BASED_CONFIG":     Callback.BASED_CONFIG,
    "BASED_INTERRUPT":  Callback.BASED_INTERRUPT,
    "BASED_QUIT":       Callback.BASED_QUIT,

    # nuqql commands
    "QUIT":             Callback.QUIT,
    "DISCONNECT":       Callback.DISCONNECT,
    "SEND_MESSAGE":     Callback.SEND_MESSAGE,
    "GET_MESSAGES":     Callback.GET_MESSAGES,
    "COLLECT_MESSAGES": Callback.COLLECT_MESSAGES,
    "ADD_ACCOUNT":      Callback.ADD_ACCOUNT,
    "DEL_ACCOUNT":      Callback.DEL_ACCOUNT,
    "UPDATE_BUDDIES":   Callback.UPDATE_BUDDIES,
    "GET_STATUS":       Callback.SET_STATUS,
    "CHAT_LIST":        Callback.CHAT_LIST,
    "CHAT_JOIN":        Callback.CHAT_JOIN,
    "CHAT_PART":        Callback.CHAT_PART,
    "CHAT_USERS":       Callback.CHAT_USERS,
    "CHAT_SEND":        Callback.CHAT_SEND,
    "CHAT_INVITE":      Callback.CHAT_INVITE,
}
