#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import socketserver
import select
import stat
import html
import sys
import os

from nuqql_based.account import ACCOUNTS, Account, store_accounts, \
        load_accounts, get_accounts
from nuqql_based.logger import LOGGERS, init_logger, init_main_logger, \
        init_account_loggers
from nuqql_based.config import CONFIG, init_config
from nuqql_based.callback import Callback, callback
from nuqql_based.message import Format


class Buddy:
    """
    Storage for buddy specific information
    """

    def __init__(self, name="none", alias="none", status="Available"):
        self.name = name
        self.alias = alias
        self.status = status


class NuqqlBaseHandler(socketserver.BaseRequestHandler):
    """
    Request Handler for the server, instantiated once per client connection.

    This is limited to one client connection at a time. It should be fine for
    our basic use case.
    """

    buffer = b""

    def handle_incoming(self):
        """
        Handle messages coming from the backend connections
        """

        # get messages from callback for each account
        for account in ACCOUNTS.values():
            messages = callback(account.aid, Callback.GET_MESSAGES, ())
            if messages:
                messages = messages.encode()
                self.request.sendall(messages)

    def handle_messages(self):
        """
        Try to find complete messages in buffer and handle each
        """

        # try to find first complete message
        eom = self.buffer.find(Format.EOM.encode())
        while eom != -1:
            # extract message from buffer
            msg = self.buffer[:eom]
            self.buffer = self.buffer[eom + 2:]

            # check if there is another complete message, for
            # next loop iteration
            eom = self.buffer.find(Format.EOM.encode())

            # start message handling
            try:
                msg = msg.decode()
            except UnicodeDecodeError as error:
                # invalid message format, drop client
                return "bye", error
            cmd, reply = handle_msg(msg)

            if cmd == "msg" and reply != "":
                # there is a message for the user, construct reply and send it
                # back to the user
                reply = reply.encode()
                self.request.sendall(reply)

            # if we need to drop the client, or exit the server, return
            if cmd in ("bye", "quit"):
                return cmd

    def handle(self):
        # self.request is the client socket
        while True:
            # handle incoming xmpp messages
            self.handle_incoming()

            # handle messages from nuqql client
            # wait 0.1 seconds for data to become available
            reads, unused_writes, errs = select.select([self.request, ], [],
                                                       [self.request, ], 0.1)
            if self.request in errs:
                # something is wrong, drop client
                return

            if self.request in reads:
                # read data from socket and add it to buffer
                self.data = self.request.recv(1024)

                # self.buffer += self.data.decode()
                self.buffer += self.data

            # handle each complete message
            cmd = self.handle_messages()

            # handle special return codes
            if cmd == "bye":
                # some error occured handling the messages or user said bye,
                # drop the client
                return
            if cmd == "quit":
                # quit the server
                sys.exit()


def handle_account_list():
    """
    List all accounts
    """

    replies = []
    for account in ACCOUNTS.values():
        reply = Format.ACCOUNT.format(account.aid, account.name, account.type,
                                      account.user, account.status)
        replies.append(reply)

    # log event
    log_msg = "account list: {0}".format(replies)
    LOGGERS["main"].info(log_msg)

    # return a single string
    return "".join(replies)


def _get_account_id():
    """
    Get next free account id
    """

    if not ACCOUNTS:
        return 0

    last_acc_id = -1
    for acc_id in sorted(ACCOUNTS.keys()):
        if acc_id - last_acc_id >= 2:
            return last_acc_id + 1
        if acc_id - last_acc_id == 1:
            last_acc_id = acc_id

    return last_acc_id + 1


def handle_account_add(params):
    """
    Add a new account.

    Expected format:
        account add xmpp robot@my_jabber_server.com my_password

    params does not include "account add"
    """

    # check if there are enough parameters
    if len(params) < 3:
        return ""

    # get account information
    acc_id = _get_account_id()
    acc_type = params[0]
    acc_user = params[1]
    acc_pass = params[2]
    new_acc = Account(aid=acc_id, atype=acc_type, user=acc_user,
                      password=acc_pass)

    # make sure the account does not exist
    for acc in ACCOUNTS.values():
        if acc.type == new_acc.type and acc.user == new_acc.user:
            return Format.INFO.format("account already exists.")

    # new account; add it
    ACCOUNTS[new_acc.aid] = new_acc

    # store updated accounts in file
    store_accounts()

    # create mew logger
    account_dir = CONFIG["dir"] / "logs" / "account" / f"{acc_id}"
    account_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(account_dir, stat.S_IRWXU)
    account_log = account_dir / "account.log"
    # logger name must be string
    new_acc.logger = init_logger(CONFIG, str(acc_id), account_log)
    # TODO: do we still need LOGGERS[acc_id]?
    LOGGERS[acc_id] = new_acc.logger
    os.chmod(account_log, stat.S_IRUSR | stat.S_IWUSR)

    # log event
    log_msg = "account new: id {0} type {1} user {2}".format(new_acc.aid,
                                                             new_acc.type,
                                                             new_acc.user)
    LOGGERS["main"].info(log_msg)

    # notify callback (if present) about new account
    callback(new_acc.aid, Callback.ADD_ACCOUNT, (new_acc, ))

    # inform caller about success
    return Format.INFO.format("new account added.")


def handle_account_delete(acc_id):
    """
    Delete an existing account

    Expected format:
        account <ID> delete
    """

    # remove account and update accounts file
    del ACCOUNTS[acc_id]
    store_accounts()

    # log event
    log_msg = "account deleted: id {0}".format(acc_id)
    LOGGERS["main"].info(log_msg)

    # notify callback (if present) about deleted account
    callback(acc_id, Callback.DEL_ACCOUNT, ())

    # inform caller about success
    return Format.INFO.format("account {} deleted.".format(acc_id))


def handle_account_buddies(acc_id, params):
    """
    Get buddies for a specific account. If params contains "online", filter
    online buddies.

    Expected format:
        account <ID> buddies [online]

    params does not include "account <ID> buddies"

    Returned messages should look like:
        buddy: <acc_id> status: <Offline/Available> name: <name> alias: <alias>
    """

    # update buddy list
    # if "update_buddies" in ACCOUNTS[acc_id].callbacks:
    #     ACCOUNTS[acc_id].callbacks["update_buddies"](ACCOUNTS[acc_id])
    callback(acc_id, Callback.UPDATE_BUDDIES, ())

    # filter online buddies?
    online = False
    if len(params) >= 1 and params[0].lower() == "online":
        online = True

    # get buddies for account
    replies = []
    for buddy in ACCOUNTS[acc_id].buddies:
        # filter online buddies if wanted by client
        if online and buddy.status != "Available":
            continue

        # construct replies
        reply = Format.BUDDY.format(acc_id, buddy.status, buddy.name,
                                    buddy.alias)
        replies.append(reply)

    # log event
    log_msg = "account {0} buddies: {1}".format(acc_id, replies)
    LOGGERS[acc_id].info(log_msg)

    # return replies as single string
    return "".join(replies)


def handle_account_collect(acc_id, params):
    """
    Collect messages for a specific account.

    Expected format:
        account <ID> collect [time]

    params does not include "account <ID> collect"
    """

    # collect all messages since <time>?
    time = 0   # TODO: change it to time of last collect?
    if len(params) >= 1:
        time = params[0]

    # log event
    log_msg = "account {0} collect {1}".format(acc_id, time)
    LOGGERS[acc_id].info(log_msg)

    # collect messages
    return callback(acc_id, Callback.COLLECT_MESSAGES, ())


def handle_account_send(acc_id, params):
    """
    Send a message to a someone over a specific account.

    Expected format:
        account <ID> send <username> <msg>

    params does not include "account <ID> send"
    """

    user = params[0]
    msg = " ".join(params[1:])      # TODO: do this better?

    # send message to user
    ACCOUNTS[acc_id].send_msg(user, msg)

    # check if it is an existing buddy
    for buddy in ACCOUNTS[acc_id].buddies:
        if buddy.name == user:
            return ""

    # new buddy; add it to account
    new_buddy = Buddy(name=user, alias="")
    ACCOUNTS[acc_id].buddies.append(new_buddy)

    # store updated accounts in file
    store_accounts()

    # log event
    log_msg = "account {0}: new buddy: {1}".format(acc_id, user)
    LOGGERS[acc_id].info(log_msg)

    return ""


def handle_account_status(acc_id, params):
    """
    Get or set current status of account

    Expected format:
        account <ID> status get
        account <ID> status set <STATUS>

    params does not include "account <ID> status"

    Returned messages for "status get" should look like:
        status: account <ID> status: <STATUS>
    """

    if not params:
        return ""

    # get current status
    if params[0] == "get":
        status = callback(acc_id, Callback.GET_STATUS, ())
        if status:
            return Format.STATUS.format(acc_id, status)

    # set current status
    if params[0] == "set":
        if len(params) < 2:
            return ""

        status = params[1]
        return callback(acc_id, Callback.SET_STATUS, (status, ))
    return ""


def handle_account_chat(acc_id, params):
    """
    Join, part, and list chats and send messages to chats

    Expected format:
        account <ID> chat list
        account <ID> chat join <CHAT>
        account <ID> chat part <CHAT>
        account <ID> chat send <CHAT> <MESSAGE>
        account <ID> chat users <CHAT>
        account <ID> chat invite <CHAT> <USER>
    """

    if not params:
        return ""

    # list active chats
    if params[0] == "list":
        return callback(acc_id, Callback.CHAT_LIST, ())

    if len(params) < 2:
        return ""

    chat = params[1]
    # join a chat
    if params[0] == "join":
        return callback(acc_id, Callback.CHAT_JOIN, (chat, ))

    # leave a chat
    if params[0] == "part":
        return callback(acc_id, Callback.CHAT_PART, (chat, ))

    # get users in chat
    if params[0] == "users":
        return callback(acc_id, Callback.CHAT_USERS, (chat, ))

    if len(params) < 3:
        return ""

    # invite a user to a chat
    if params[0] == "invite":
        user = params[2]
        return callback(acc_id, Callback.CHAT_INVITE, (chat, user))

    # send a message to a chat
    if params[0] == "send":
        msg = " ".join(params[2:])
        return callback(acc_id, Callback.CHAT_SEND, (chat, msg))

    return ""


# def handleAccount(parts, account, command, params):
def handle_account(parts):
    """
    Handle account specific commands received from client
    """

    if parts[1] == "list":
        # special case for "list" command
        command = parts[1]
    elif parts[1] == "add":
        # special case for "add" command
        command = parts[1]
        params = parts[2:]
    elif len(parts) >= 3:
        # account specific commands
        try:
            acc_id = int(parts[1])
        except ValueError:
            return Format.ERROR.format("invalid account ID")
        command = parts[2]
        params = parts[3:]
        # valid account?
        if acc_id not in ACCOUNTS.keys():
            return Format.ERROR.format("invalid account")
    else:
        # invalid command, ignore
        return Format.ERROR.format("invalid command")

    if command == "list":
        return handle_account_list()

    if command == "add":
        # TODO: currently this supports
        # "account <ID> add" and "account add <ID>", OK?
        return handle_account_add(params)

    if command == "delete":
        return handle_account_delete(acc_id)

    if command == "buddies":
        return handle_account_buddies(acc_id, params)

    if command == "collect":
        return handle_account_collect(acc_id, params)

    if command == "send":
        return handle_account_send(acc_id, params)

    if command == "status":
        return handle_account_status(acc_id, params)

    if command == "chat":
        return handle_account_chat(acc_id, params)

    return Format.ERROR.format("unknown command")


def handle_msg(msg):
    """
    Handle messages received from client
    """

    # get parts of message
    parts = msg.split(" ")

    # account specific commands
    if len(parts) >= 2 and parts[0] == "account":
        return ("msg", handle_account(parts))

    # handle "bye" and "quit" commands
    if parts[0] in ("bye", "quit"):
        # call disconnect or quit callback in every account
        for acc in get_accounts().values():
            if parts[0] == "bye":
                callback(acc.aid, Callback.DISCONNECT, ())
            if parts[0] == "quit":
                callback(acc.aid, Callback.QUIT, ())
        return (parts[0], "Goodbye.")

    # handle "help" command
    if parts[0] == "help":
        return ("msg", Format.HELP_MSG)

    # others
    # TODO: ver? who?
    # ignore rest for now...
    return ("msg", "")


def format_message(account, tstamp, sender, destination, msg):
    """
    Helper for formatting "message" messages
    """

    msg_body = html.escape(msg)
    msg_body = "<br/>".join(msg_body.split("\n"))
    return Format.MESSAGE.format(account.aid, destination, tstamp, sender,
                                 msg_body)


def format_chat_msg(account, tstamp, sender, destination, msg):
    """
    Helper for formatting "chat msg" messages
    """

    msg_body = html.escape(msg)
    msg_body = "<br/>".join(msg_body.split("\n"))
    return Format.CHAT_MSG.format(account.aid, destination, tstamp, sender,
                                  msg_body)


def run_inet_server(config):
    """
    Run an AF_INET server
    """

    listen = (config["address"], config["port"])
    with socketserver.TCPServer(listen, NuqqlBaseHandler,
                                bind_and_activate=False) as server:
        server.allow_reuse_address = True
        server.server_bind()
        server.server_activate()
        server.serve_forever()


def run_unix_server(config):
    """
    Run an AF_UNIX server
    """

    # make sure paths exist
    config["dir"].mkdir(parents=True, exist_ok=True)
    sockfile = str(config["dir"] / config["sockfile"])
    try:
        # unlink sockfile of previous execution of the server
        os.unlink(sockfile)
    except FileNotFoundError:
        # ignore if the file did not exist
        pass
    with socketserver.UnixStreamServer(sockfile, NuqqlBaseHandler) as server:
        os.chmod(sockfile, stat.S_IRUSR | stat.S_IWUSR)
        server.serve_forever()


def run_server(config):
    """
    Run the server; can be AF_INET or AF_UNIX.
    """

    if config["daemonize"]:
        # exit if we cannot load the daemon module
        try:
            import daemon
        except ImportError:
            print("Could not load python module \"daemon\", "
                  "no daemonize support.")
            return

        # daemonize the server
        with daemon.DaemonContext():
            if config["af"] == "inet":
                run_inet_server(config)
            elif config["af"] == "unix":
                run_unix_server(config)
    else:
        # run in foreground
        if config["af"] == "inet":
            run_inet_server(config)
        elif config["af"] == "unix":
            run_unix_server(config)


def main():
    """
    Main function
    """

    # initialize configuration from command line and config file
    config = init_config()

    # initialize main logger
    init_main_logger(config)

    # load accounts
    load_accounts()

    # initialize account loggers
    init_account_loggers(config, ACCOUNTS)

    # start server
    try:
        run_server(config)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
