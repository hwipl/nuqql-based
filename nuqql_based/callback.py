"""
Nuqql-based callbacks
"""

from enum import Enum, auto

CALLBACKS = {}


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

    _cb_map = {
        # based events
        "BASED_CONFIG":     BASED_CONFIG,
        "BASED_INTERRUPT":  BASED_INTERRUPT,
        "BASED_QUIT":       BASED_QUIT,

        # nuqql commands
        "QUIT":             QUIT,
        "DISCONNECT":       DISCONNECT,
        "SEND_MESSAGE":     SEND_MESSAGE,
        "GET_MESSAGES":     GET_MESSAGES,
        "COLLECT_MESSAGES": COLLECT_MESSAGES,
        "ADD_ACCOUNT":      ADD_ACCOUNT,
        "DEL_ACCOUNT":      DEL_ACCOUNT,
        "UPDATE_BUDDIES":   UPDATE_BUDDIES,
        "GET_STATUS":       SET_STATUS,
        "CHAT_LIST":        CHAT_LIST,
        "CHAT_JOIN":        CHAT_JOIN,
        "CHAT_PART":        CHAT_PART,
        "CHAT_USERS":       CHAT_USERS,
        "CHAT_SEND":        CHAT_SEND,
        "CHAT_INVITE":      CHAT_INVITE,
    }

    @staticmethod
    def parse(name):
        """
        Map callback name to callback
        """

        return Callback._cb_map[name]


def callback(account_id, cb_name, params):
    """
    Call callback if it is registered
    """

    if cb_name in CALLBACKS:
        return CALLBACKS[cb_name](account_id, cb_name, params)

    return ""


def register_callback(cb_name, cb_func):
    """
    Register a callback
    """

    CALLBACKS[cb_name] = cb_func


def unregister_callback(cb_name):
    """
    Unregister a callback
    """

    if cb_name in CALLBACKS:
        del CALLBACKS[cb_name]
