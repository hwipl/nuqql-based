"""
Nuqql message formats
"""

import html
from enum import Enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql_based.account import Account  # noqa
    from nuqql_based.buddy import Buddy  # noqa


class Message(str, Enum):
    """
    Message format strings
    """

    EOM = "\r\n"
    INFO = "info: {0}" + EOM
    ERROR = "error: {0}" + EOM
    ACCOUNT = "account: {0} ({1}) {2} {3} [{4}]" + EOM
    BUDDY = "buddy: {0} status: {1} name: {2} alias: {3}" + EOM
    STATUS = "status: account {0} status: {1}" + EOM
    MESSAGE = "message: {0} {1} {2} {3} {4}" + EOM
    CHAT_USER = "chat: user: {0} {1} {2} {3} {4}" + EOM
    CHAT_LIST = "chat: list: {0} {1} {2} {3}" + EOM
    CHAT_MSG = "chat: msg: {0} {1} {2} {3} {4}" + EOM

    # help message
    HELP_MSG = """info: List of commands and their description:
account list
    list all accounts and their account ids.
account add <protocol> <user> <password>
    add a new account for chat protocol <protocol> with user name <user> and
    the password <password>. The supported chat protocol(s) are backend
    specific. The user name is chat protocol specific. An account id is
    assigned to the account that can be shown with "account list".
account <id> delete
    delete the account with the account id <id>.
account <id> buddies [online]
    list all buddies on the account with the account id <id>. Optionally, show
    only online buddies with the extra parameter "online".
account <id> collect
    collect all messages received on the account with the account id <id>.
account <id> send <user> <msg>
    send a message to the user <user> on the account with the account id <id>.
account <id> status get
    get the status of the account with the account id <id>.
account <id> status set <status>
    set the status of the account with the account id <id> to <status>.
account <id> chat list
    list all group chats on the account with the account id <id>.
account <id> chat join <chat>
    join the group chat <chat> on the account with the account id <id>.
account <id> chat part <chat>
    leave the group chat <chat> on the account with the account id <id>.
account <id> chat send <chat> <msg>
    send the message <msg> to the group chat <chat> on the account with the
    account id <id>.
account <id> chat users <chat>
    list the users in the group chat <chat> on the account with the
    account id <id>.
account <id> chat invite <chat> <user>
    invite the user <user> to the group chat <chat> on the account with the
    account id <id>.
version
    get version of the backend
bye
    disconnect from backend
quit
    quit backend
help
    show this help""" + EOM

    def __str__(self) -> str:
        return str(self.value)

    @staticmethod
    def info(info_text: str) -> str:
        """
        Helper for formatting an "info" message
        """

        return str(Message.INFO).format(info_text)

    @staticmethod
    def error(error_text: str) -> str:
        """
        Helper for formatting an "error" message
        """

        return str(Message.ERROR).format(error_text)

    @staticmethod
    def account(acc: "Account") -> str:
        """
        Helper for formatting an "account" message
        """

        return str(Message.ACCOUNT).format(acc.aid, acc.name, acc.type,
                                           acc.user, acc.status)

    @staticmethod
    def buddy(account: "Account", buddy: "Buddy") -> str:
        """
        Helper for formatting a "buddy" message
        """
        return str(Message.BUDDY).format(account.aid, buddy.status, buddy.name,
                                         buddy.alias)

    @staticmethod
    def status(account: "Account", status: str) -> str:
        """
        Helper for formatting a "status" message
        """

        return str(Message.STATUS).format(account.aid, status)

    @staticmethod
    def message(account: "Account", tstamp: str, sender: str, destination: str,
                msg: str) -> str:
        """
        Helper for formatting "message" messages
        """

        msg_body = html.escape(msg)
        msg_body = "<br/>".join(msg_body.split("\n"))
        return str(Message.MESSAGE).format(account.aid, destination, tstamp,
                                           sender, msg_body)

    @staticmethod
    def chat_user(account: "Account", chat: str, sender_id: str,
                  sender_name: str, status: str) -> str:
        """
        Helper for formatting a "chat user" message
        """

        return str(Message.CHAT_USER).format(account.aid, chat, sender_id,
                                             sender_name, status)

    @staticmethod
    def chat_list(account: "Account", chat_id: str, chat_name: str,
                  user: str) -> str:
        """
        Helper for formatting a "chat list" message
        """

        return str(Message.CHAT_LIST).format(account.aid, chat_id, chat_name,
                                             user)

    @staticmethod
    def chat_msg(account: "Account", tstamp: str, sender: str,
                 destination: str, msg: str) -> str:
        """
        Helper for formatting "chat msg" messages
        """

        msg_body = html.escape(msg)
        msg_body = "<br/>".join(msg_body.split("\n"))
        return str(Message.CHAT_MSG).format(account.aid, destination, tstamp,
                                            sender, msg_body)

    @staticmethod
    def is_message(msg: str) -> bool:
        """
        Helper for detecting if message (string) is a "message" or
        "chat message" message.
        """

        if msg.startswith("chat: msg:") or \
           msg.startswith("message:"):
            return True

        return False
