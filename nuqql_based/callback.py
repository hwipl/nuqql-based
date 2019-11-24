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
