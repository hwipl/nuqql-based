"""
Nuqql message formats
"""

import html

from enum import Enum


class Format(str, Enum):
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
bye
    disconnect from backend
quit
    quit backend
help
    show this help""" + EOM

    def __str__(self):
        return str(self.value)

    @staticmethod
    def message(account, tstamp, sender, destination, msg):
        """
        Helper for formatting "message" messages
        """

        msg_body = html.escape(msg)
        msg_body = "<br/>".join(msg_body.split("\n"))
        return Format.MESSAGE.format(account.aid, destination, tstamp, sender,
                                     msg_body)

    @staticmethod
    def chat_msg(account, tstamp, sender, destination, msg):
        """
        Helper for formatting "chat msg" messages
        """

        msg_body = html.escape(msg)
        msg_body = "<br/>".join(msg_body.split("\n"))
        return Format.CHAT_MSG.format(account.aid, destination, tstamp,
                                      sender, msg_body)
