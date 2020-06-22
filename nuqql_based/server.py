"""
nuqql-based socket server
"""

import socketserver
import logging
import select
import stat
import sys
import os
try:
    import daemon   # type: ignore
except ImportError:
    daemon = None

from typing import TYPE_CHECKING, List, Tuple, Optional

from nuqql_based.callback import Callback
from nuqql_based.message import Message

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql_based.config import Config  # noqa
    from nuqql_based.callback import Callbacks  # noqa
    from nuqql_based.account import Account, AccountList  # noqa


class _TCPServer(socketserver.TCPServer):
    def __init__(self, listen, handler, based_server):
        self.allow_reuse_address = True
        super().__init__(listen, handler)
        self.based_server = based_server


class _UnixStreamServer(socketserver.UnixStreamServer):
    def __init__(self, listen, handler, based_server):
        super().__init__(listen, handler)
        self.based_server = based_server


class _Handler(socketserver.BaseRequestHandler):
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
        based_server = self.server.based_server
        callbacks = based_server.callbacks
        account_list = based_server.account_list
        accounts = account_list.get()
        for acc in accounts.values():
            messages = acc.get_messages()
            # TODO: this expects a list. change to string? document list req?
            messages += callbacks.call(Callback.GET_MESSAGES, acc, ())
            for msg in messages:
                msg = msg.encode()
                self.request.sendall(msg)

    def handle_messages(self):
        """
        Try to find complete messages in buffer and handle each
        """

        # try to find first complete message
        eom = self.buffer.find(Message.EOM.encode())
        while eom != -1:
            # extract message from buffer
            msg = self.buffer[:eom]
            self.buffer = self.buffer[eom + 2:]

            # check if there is another complete message, for
            # next loop iteration
            eom = self.buffer.find(Message.EOM.encode())

            # start message handling
            try:
                msg = msg.decode()
            except UnicodeDecodeError as error:
                # invalid message format, drop client
                return "bye", error
            cmd, reply = self.server.based_server.handle_msg(msg)

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

        # push accounts to client if "push-accounts" is configured
        based_server = self.server.based_server
        if based_server.config.get_push_accounts():
            accounts = based_server.handle_account_list()
            if accounts:
                self.request.sendall(accounts.encode())

        while True:
            # handle incoming messages
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


class Server:
    """
    Based server class
    """

    def __init__(self, config: "Config", callbacks: "Callbacks",
                 account_list: "AccountList") -> None:
        self.server: Optional[socketserver.BaseServer] = None
        self.config = config
        self.callbacks = callbacks
        self.account_list = account_list

    def _run_inet(self) -> None:
        """
        Run an AF_INET server
        """

        listen = (self.config.get_address(), self.config.get_port())
        with _TCPServer(listen, _Handler, self) as server:
            self.server = server
            server.serve_forever()

    def _run_unix(self) -> None:
        """
        Run an AF_UNIX server
        """

        # make sure paths exist
        self.config.get_dir().mkdir(parents=True, exist_ok=True)
        sockfile = str(self.config.get_dir() / self.config.get_sockfile())
        try:
            # unlink sockfile of previous execution of the server
            os.unlink(sockfile)
        except FileNotFoundError:
            # ignore if the file did not exist
            pass
        with _UnixStreamServer(sockfile, _Handler, self) as server:
            os.chmod(sockfile, stat.S_IRUSR | stat.S_IWUSR)
            self.server = server
            server.serve_forever()

    def run(self) -> None:
        """
        Run the server; can be AF_INET or AF_UNIX.
        """

        if self.config.get_daemonize():
            # exit if we cannot load the daemon module
            if not daemon:
                print("Could not load python module \"daemon\", "
                      "no daemonize support.")
                return

            # daemonize the server
            with daemon.DaemonContext():
                if self.config.get_af() == "inet":
                    self._run_inet()
                elif self.config.get_af() == "unix":
                    self._run_unix()
        else:
            # run in foreground
            if self.config.get_af() == "inet":
                self._run_inet()
            elif self.config.get_af() == "unix":
                self._run_unix()

    def handle_account_list(self) -> str:
        """
        List all accounts
        """

        replies = []
        accounts = self.account_list.get()
        for acc in accounts.values():
            reply = Message.account(acc)
            replies.append(reply)

        # inform caller that all accounts have been received
        replies.append(Message.info("listed accounts."))

        # log event
        log_msg = "account list: {0}".format(replies)
        logging.info(log_msg)

        # return a single string
        return "".join(replies)

    def _handle_account_add(self, params: List[str]) -> str:
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
        acc_type = params[0]
        acc_user = params[1]
        acc_pass = params[2]

        # add account
        result = self.account_list.add(acc_type, acc_user, acc_pass)

        # inform caller about result
        return result

    def _handle_account_delete(self, acc_id: int) -> str:
        """
        Delete an existing account

        Expected format:
            account <ID> delete
        """

        # delete account
        result = self.account_list.delete(acc_id)

        # inform caller about result
        return Message.info(result)

    def _handle_account_buddies(self, acc_id: int, params: List[str]) -> str:
        """
        Get buddies for a specific account. If params contains "online", filter
        online buddies.

        Expected format:
            account <ID> buddies [online]

        params does not include "account <ID> buddies"

        Returned messages should look like:
            buddy: <acc_id> status: <Offline/Available> name: <name> alias:
                <alias>
        """

        # get account
        accounts = self.account_list.get()
        acc = accounts[acc_id]

        # update buddy list
        self.callbacks.call(Callback.UPDATE_BUDDIES, acc, ())

        # filter online buddies?
        online = False
        if len(params) >= 1 and params[0].lower() == "online":
            online = True

        # get buddies for account
        replies = []
        for buddy in acc.get_buddies():
            # filter online buddies if wanted by client
            if online and buddy.status != "Available":
                continue

            # construct replies
            reply = Message.buddy(acc, buddy)
            replies.append(reply)

        # add info message that all buddies have been received
        replies.append(Message.info(f"got buddies for account {acc_id}."))

        # log event
        log_msg = "account {0} buddies: {1}".format(acc_id, replies)
        logging.info(log_msg)

        # return replies as single string
        return "".join(replies)

    def _handle_account_collect(self, acc_id: int, params: List[str]) -> str:
        """
        Collect messages for a specific account.

        Expected format:
            account <ID> collect [time]

        params does not include "account <ID> collect"
        """

        # collect all messages since <time>?
        time = 0   # TODO: change it to time of last collect?
        if len(params) >= 1:
            time = int(params[0])

        # log event
        log_msg = "account {0} collect {1}".format(acc_id, time)
        logging.info(log_msg)

        # collect messages
        accounts = self.account_list.get()
        acc = accounts[acc_id]
        history = acc.get_history()
        # TODO: this expects a list. change to string? document list req?
        history += self.callbacks.call(Callback.COLLECT_MESSAGES, acc, ())

        # append info message to notify caller that everything was collected
        history += [Message.info(f"collected messages for account {acc_id}.")]

        # return history as single string
        return "".join(history)

    def _handle_account_send(self, acc_id: int, params: List[str]) -> str:
        """
        Send a message to a someone over a specific account.

        Expected format:
            account <ID> send <username> <msg>

        params does not include "account <ID> send"
        """

        user = params[0]
        msg = " ".join(params[1:])      # TODO: do this better?

        # send message to user
        accounts = self.account_list.get()
        accounts[acc_id].send_msg(user, msg)

        return ""

    def _handle_account_status(self, acc_id: int, params: List[str]) -> str:
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

        # get account
        accounts = self.account_list.get()
        acc = accounts[acc_id]

        # get current status
        if params[0] == "get":
            status = self.callbacks.call(Callback.GET_STATUS, acc, ())
            if status:
                return Message.status(acc, status)

        # set current status
        if params[0] == "set":
            if len(params) < 2:
                return ""

            status = params[1]
            return self.callbacks.call(Callback.SET_STATUS, acc, (status, ))
        return ""

    def _handle_account_chat_2_params(self, cmd: str, acc: "Account",
                                      chat: str) -> str:
        # join a chat
        if cmd == "join":
            return self.callbacks.call(Callback.CHAT_JOIN, acc, (chat, ))

        # leave a chat
        if cmd == "part":
            return self.callbacks.call(Callback.CHAT_PART, acc, (chat, ))

        # get users in chat
        if cmd == "users":
            return self.callbacks.call(Callback.CHAT_USERS, acc, (chat, ))

        return ""

    def _handle_account_chat_3plus_params(self, acc: "Account",
                                          params: List[str]) -> str:
        cmd = params[0]
        chat = params[1]

        # invite a user to a chat
        if cmd == "invite":
            user = params[2]
            return self.callbacks.call(Callback.CHAT_INVITE, acc, (chat, user))

        # send a message to a chat
        if cmd == "send":
            msg = " ".join(params[2:])
            return self.callbacks.call(Callback.CHAT_SEND, acc, (chat, msg))

        return ""

    def _handle_account_chat(self, acc_id: int, params: List[str]) -> str:
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

        # get account
        accounts = self.account_list.get()
        acc = accounts[acc_id]

        # list active chats
        if params[0] == "list":
            return self.callbacks.call(Callback.CHAT_LIST, acc, ())

        if len(params) == 2:
            cmd = params[0]
            chat = params[1]
            return self._handle_account_chat_2_params(cmd, acc, chat)

        if len(params) >= 3:
            return self._handle_account_chat_3plus_params(acc, params)

        return ""

    def _handle_account_command(self, command: str, acc_id: int,
                                params: List[str]) -> str:
        if command == "list":
            return self.handle_account_list()

        if command == "add":
            # currently this supports "account <ID> add" and "account add <ID>"
            # if the account ID is valid
            return self._handle_account_add(params)

        if command == "delete":
            return self._handle_account_delete(acc_id)

        # handle other commands with same parameters
        command_map = {
            "buddies": self._handle_account_buddies,
            "collect": self._handle_account_collect,
            "send": self._handle_account_send,
            "status": self._handle_account_status,
            "chat": self._handle_account_chat,
        }
        if command in command_map:
            return command_map[command](acc_id, params)

        return Message.error("unknown command")

    def _handle_account(self, parts: List[str]) -> str:
        """
        Handle account specific commands received from client
        """

        # prepare everything for the actual command handling later
        acc_id = -1
        params = []
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
                return Message.error("invalid account ID")
            command = parts[2]
            params = parts[3:]
            # valid account?
            if acc_id not in self.account_list.get().keys():
                return Message.error("invalid account")
        else:
            # invalid command, ignore
            return Message.error("invalid command")

        return self._handle_account_command(command, acc_id, params)

    def _handle_version(self) -> Tuple[str, str]:
        """
        Handle the version command received from client
        """

        msg = self.callbacks.call(Callback.VERSION, None, ())
        if not msg:
            name = self.config.get_name()
            version = self.config.get_version()
            msg = f"version: {name} v{version}"
        return ("msg", Message.info(msg))

    def handle_msg(self, msg: str) -> Tuple[str, str]:
        """
        Handle messages received from client
        """

        # get parts of message
        parts = msg.split(" ")

        # account specific commands
        if len(parts) >= 2 and parts[0] == "account":
            return ("msg", self._handle_account(parts))

        # handle "bye" and "quit" commands
        if parts[0] in ("bye", "quit"):
            # call disconnect or quit callback in every account
            for acc in self.account_list.get().values():
                if parts[0] == "bye":
                    self.callbacks.call(Callback.DISCONNECT, acc, ())
                if parts[0] == "quit":
                    self.callbacks.call(Callback.QUIT, acc, ())
            return (parts[0], "Goodbye.")

        # handle "help" command
        if parts[0] == "help":
            return ("msg", Message.HELP_MSG)

        if parts[0] == "version":
            return self._handle_version()

        # others
        # TODO: who?
        # ignore rest for now...
        return ("msg", "")
