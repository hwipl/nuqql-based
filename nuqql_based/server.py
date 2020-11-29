"""
nuqql-based socket server
"""

import asyncio
import logging
import stat
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


class Server:
    """
    Based server class
    """

    def __init__(self, config: "Config", callbacks: "Callbacks",
                 account_list: "AccountList", queue: asyncio.Queue) -> None:
        self.server: Optional[asyncio.AbstractServer] = None
        self.config = config
        self.callbacks = callbacks
        self.account_list = account_list
        self.queue = queue
        self.connected = False

    async def _handle_incoming(self, writer: asyncio.StreamWriter) -> None:
        """
        Handle messages coming from the backend connections
        """

        try:
            # read messages from message queue
            while True:
                msg = await self.queue.get()
                writer.write(msg.encode())
                await writer.drain()
                self.queue.task_done()
        except asyncio.CancelledError:
            return

    async def _handle_messages(self, reader: asyncio.StreamReader, writer:
                               asyncio.StreamWriter) -> str:
        """
        Try to find complete messages in buffer and handle each
        """

        # try to find first complete message
        try:
            data = await reader.readuntil(Message.EOM.encode())
        except asyncio.IncompleteReadError:
            return "bye"

        # start message handling
        try:
            msg = data[:-2].decode()
        except UnicodeDecodeError:
            # invalid message format, drop client
            return "bye"
        cmd, reply = await self.handle_msg(msg)

        if cmd == "msg" and reply != "":
            # there is a message for the user, construct reply and send it
            # back to the user
            writer.write(reply.encode())
            await writer.drain()

        # return message/command
        return cmd

    async def _handle_client(self, reader: asyncio.StreamReader, writer:
                             asyncio.StreamWriter) -> None:
        """
        Handle client connection
        """

        # only accept one client at a time
        if self.connected:
            writer.close()
            await writer.wait_closed()
            return
        self.connected = True

        # if present, send welcome message to client
        welcome = await self.callbacks.call(Callback.HELP_WELCOME, None, ())
        if welcome:
            writer.write(welcome.encode())
            await writer.drain()

        # send accounts to new client if "push accounts" is enabled
        if self.config.get_push_accounts():
            accounts = await self.handle_account_list()
            if not accounts:
                # return account adding help
                accounts = await self.callbacks.call(Callback.HELP_ACCOUNT_ADD,
                                                     None, ())
            if accounts:
                writer.write(accounts.encode())
                await writer.drain()

        # start sending incoming messages to client
        inc_task = asyncio.create_task(self._handle_incoming(writer))

        while True:

            # handle each complete message
            cmd = await self._handle_messages(reader, writer)

            # handle special return codes
            if cmd in ("bye", "quit"):
                # some error occured handling the messages or
                # user said bye/quit, drop the client
                inc_task.cancel()
                await inc_task
                writer.close()
                await writer.wait_closed()
                self.connected = False
                if cmd == "quit":
                    # quit the server
                    assert self.server
                    self.server.close()
                    await self.server.wait_closed()
                return

    async def _run_inet(self) -> None:
        """
        Run an AF_INET server
        """

        server = await asyncio.start_server(
            self._handle_client, self.config.get_address(),
            self.config.get_port())

        async with server:
            self.server = server
            await server.serve_forever()

    async def _run_unix(self) -> None:
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

        server = await asyncio.start_unix_server(
             self._handle_client, sockfile, start_serving=False)

        async with server:
            os.chmod(sockfile, stat.S_IRUSR | stat.S_IWUSR)
            self.server = server
            await server.serve_forever()

    async def run(self) -> None:
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
                    await self._run_inet()
                elif self.config.get_af() == "unix":
                    await self._run_unix()
        else:
            # run in foreground
            if self.config.get_af() == "inet":
                await self._run_inet()
            elif self.config.get_af() == "unix":
                await self._run_unix()

    async def handle_account_list(self) -> str:
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

        # add account add help if there are no accounts
        if not accounts:
            replies.append(await self.callbacks.call(Callback.HELP_ACCOUNT_ADD,
                                                     None, ()))

        # log event
        log_msg = "account list: {0}".format(replies)
        logging.info(log_msg)

        # return a single string
        return "".join(replies)

    async def _handle_account_add(self, params: List[str]) -> str:
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
        result = await self.account_list.add(acc_type, acc_user, acc_pass)

        # inform caller about result
        return result

    async def _handle_account_delete(self, acc_id: int) -> str:
        """
        Delete an existing account

        Expected format:
            account <ID> delete
        """

        # delete account
        result = await self.account_list.delete(acc_id)

        # inform caller about result
        return Message.info(result)

    async def _handle_account_buddies(self, acc_id: int,
                                      params: List[str]) -> str:
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

        # filter online buddies?
        online = False
        if len(params) >= 1 and params[0].lower() == "online":
            online = True

        # update buddy list
        result = await self.callbacks.call(Callback.GET_BUDDIES, acc,
                                           (online,))

        # add info message that all buddies have been received
        info = Message.info(f"got buddies for account {acc_id}.")

        # log event
        log_msg = "account {0} buddies: {1}".format(acc_id, result)
        logging.info(log_msg)

        # return replies as single string
        return result + info

    async def _handle_account_collect(self, acc_id: int,
                                      params: List[str]) -> str:
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
        history += await self.callbacks.call(Callback.COLLECT_MESSAGES, acc,
                                             ())

        # append info message to notify caller that everything was collected
        history += [Message.info(f"collected messages for account {acc_id}.")]

        # return history as single string
        return "".join(history)

    async def _handle_account_send(self, acc_id: int,
                                   params: List[str]) -> str:
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
        await accounts[acc_id].send_msg(user, msg)

        return ""

    async def _handle_account_status(self, acc_id: int,
                                     params: List[str]) -> str:
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
            status = await self.callbacks.call(Callback.GET_STATUS, acc, ())
            if status:
                return Message.status(acc, status)

        # set current status
        if params[0] == "set":
            if len(params) < 2:
                return ""

            status = params[1]
            return await self.callbacks.call(Callback.SET_STATUS, acc,
                                             (status, ))
        return ""

    async def _handle_account_chat_2_params(self, cmd: str, acc: "Account",
                                            chat: str) -> str:
        # join a chat
        if cmd == "join":
            return await self.callbacks.call(Callback.CHAT_JOIN, acc, (chat, ))

        # leave a chat
        if cmd == "part":
            return await self.callbacks.call(Callback.CHAT_PART, acc, (chat, ))

        # get users in chat
        if cmd == "users":
            return await self.callbacks.call(Callback.CHAT_USERS, acc,
                                             (chat, ))

        return ""

    async def _handle_account_chat_3plus_params(self, acc: "Account",
                                                params: List[str]) -> str:
        cmd = params[0]
        chat = params[1]

        # invite a user to a chat
        if cmd == "invite":
            user = params[2]
            return await self.callbacks.call(Callback.CHAT_INVITE, acc,
                                             (chat, user))

        # send a message to a chat
        if cmd == "send":
            msg = " ".join(params[2:])
            return await self.callbacks.call(Callback.CHAT_SEND, acc,
                                             (chat, msg))

        return ""

    async def _handle_account_chat(self, acc_id: int,
                                   params: List[str]) -> str:
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
            return await self.callbacks.call(Callback.CHAT_LIST, acc, ())

        if len(params) == 2:
            cmd = params[0]
            chat = params[1]
            return await self._handle_account_chat_2_params(cmd, acc, chat)

        if len(params) >= 3:
            return await self._handle_account_chat_3plus_params(acc, params)

        return ""

    async def _handle_account_command(self, command: str, acc_id: int,
                                      params: List[str]) -> str:
        if command == "list":
            return await self.handle_account_list()

        if command == "add":
            # currently this supports "account <ID> add" and "account add <ID>"
            # if the account ID is valid
            return await self._handle_account_add(params)

        if command == "delete":
            return await self._handle_account_delete(acc_id)

        # handle other commands with same parameters
        command_map = {
            "buddies": self._handle_account_buddies,
            "collect": self._handle_account_collect,
            "send": self._handle_account_send,
            "status": self._handle_account_status,
            "chat": self._handle_account_chat,
        }
        if command in command_map:
            return await command_map[command](acc_id, params)

        return Message.error("unknown command")

    async def _handle_account(self, parts: List[str]) -> str:
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

        return await self._handle_account_command(command, acc_id, params)

    async def _handle_version(self) -> Tuple[str, str]:
        """
        Handle the version command received from client
        """

        msg = await self.callbacks.call(Callback.VERSION, None, ())
        if not msg:
            name = self.config.get_name()
            version = self.config.get_version()
            msg = f"version: {name} v{version}"
        return ("msg", Message.info(msg))

    async def handle_msg(self, msg: str) -> Tuple[str, str]:
        """
        Handle messages received from client
        """

        # get parts of message
        parts = msg.split(" ")

        # account specific commands
        if len(parts) >= 2 and parts[0] == "account":
            return ("msg", await self._handle_account(parts))

        # handle "bye" and "quit" commands
        if parts[0] in ("bye", "quit"):
            # call disconnect or quit callback in every account
            for acc in self.account_list.get().values():
                if parts[0] == "bye":
                    await self.callbacks.call(Callback.DISCONNECT, acc, ())
                if parts[0] == "quit":
                    await self.callbacks.call(Callback.QUIT, acc, ())
            return (parts[0], "Goodbye.")

        # handle "help" command
        if parts[0] == "help":
            return ("msg", Message.HELP_MSG)

        if parts[0] == "version":
            return await self._handle_version()

        # others
        # TODO: who?
        # ignore rest for now...
        return ("msg", "")
