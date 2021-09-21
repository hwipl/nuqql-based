"""
Nuqql-based accounts
"""

import configparser
import logging
import asyncio
import stat
import os

from typing import TYPE_CHECKING, List, Dict

from nuqql_based.callback import Callback
from nuqql_based.message import Message

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from logging import Logger  # noqa
    from nuqql_based.callback import Callbacks  # noqa
    from nuqql_based.config import Config  # noqa


# pylint: disable=too-many-instance-attributes
class Account:
    """
    Storage for account specific information
    """

    def __init__(self, config: "Config", callbacks: "Callbacks",
                 queue: asyncio.Queue, aid: int = 0) -> None:
        self.aid = aid
        self.name = ""
        self.type = "dummy"
        self.user = "dummy@dummy.com"
        self.password = "dummy_password"
        self.status = "online"
        self._history: List[str] = []
        self.config = config
        self.callbacks = callbacks
        self.queue = queue

    async def send_msg(self, user: str, msg: str) -> None:
        """
        Send message to user.
        """

        # try to send message
        if self.callbacks:
            await self.callbacks.call(Callback.SEND_MESSAGE, self, (user, msg))

        # log message
        log_msg = f"message: to {user}: {msg}"
        logging.info(log_msg)

    def receive_msg(self, msg: str) -> None:
        """
        Receive a message from other users or the backend
        """

        self.queue.put_nowait(msg)

        if Message.is_message(msg) and self.config.get_history():
            # TODO: add timestamp?
            self._history.append(msg)

    def get_history(self) -> List[str]:
        """
        Get the message history
        """

        # TODO: add timestamp parameter?
        history = self._history[:]

        return history


class AccountList:
    """
    List of all accounts
    """

    def __init__(self, config: "Config", callbacks: "Callbacks",
                 queue: asyncio.Queue) -> None:
        self.config = config
        self.callbacks = callbacks
        self.queue = queue
        self.accounts: Dict[int, Account] = {}

    def store(self) -> None:
        """
        Store accounts in a file.
        """

        # set accounts file and init configparser
        accounts_file = self.config.get_dir() / "accounts.ini"
        accconf = configparser.ConfigParser()
        accconf.optionxform = lambda option: option     # type: ignore

        # construct accounts config that will be written to the accounts file
        for acc in self.accounts.values():
            section = f"account {acc.aid}"
            accconf[section] = {}
            accconf[section]["id"] = str(acc.aid)
            accconf[section]["type"] = acc.type
            accconf[section]["user"] = acc.user
            accconf[section]["password"] = acc.password

        try:
            with open(accounts_file, "w", encoding='UTF-8') as acc_file:
                # make sure only user can read/write file before storing
                # anything
                os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

                # write accounts to file
                accconf.write(acc_file)
        except (OSError, configparser.Error) as error:
            error_msg = f"Error storing accounts file: {error}"
            logging.error(error_msg)

    async def load(self) -> Dict[int, Account]:
        """
        Load accounts from a file.
        """

        # make sure path and file exist
        self.config.get_dir().mkdir(parents=True, exist_ok=True)
        os.chmod(self.config.get_dir(), stat.S_IRWXU)
        accounts_file = self.config.get_dir() / "accounts.ini"
        if not accounts_file.exists():
            return self.accounts

        # make sure only user can read/write file before using it
        os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

        # read config file
        try:
            accconf = configparser.ConfigParser()
            accconf.read(accounts_file)
        except configparser.Error as error:
            error_msg = f"Error loading accounts file: {error}"
            logging.error(error_msg)

        for section in accconf.sections():
            # try to read account from account file
            try:
                acc_id = int(accconf[section]["id"])
                acc_type = accconf[section]["type"]
                acc_user = accconf[section]["user"]
                acc_pass = accconf[section]["password"]
            except KeyError as error:
                error_msg = f"Error loading account: {error}"
                logging.error(error_msg)
                continue

            # add account
            await self.add(acc_type, acc_user, acc_pass, acc_id=acc_id)

        return self.accounts

    def get(self) -> Dict[int, Account]:
        """
        Helper for getting the accounts
        """

        return self.accounts

    def _get_free_account_id(self) -> int:
        """
        Get next free account id
        """

        if not self.accounts:
            return 0

        last_acc_id = -1
        for acc_id in sorted(self.accounts.keys()):
            if acc_id - last_acc_id >= 2:
                return last_acc_id + 1
            if acc_id - last_acc_id == 1:
                last_acc_id = acc_id

        return last_acc_id + 1

    async def add(self, acc_type: str, acc_user: str, acc_pass: str,
                  acc_id: int = None) -> str:
        """
        Add a new account
        """

        # make sure the account does not exist
        for acc in self.accounts.values():
            if acc.type == acc_type and acc.user == acc_user:
                return Message.info("account already exists.")

        # get a free account id if none is given
        if acc_id is None:
            acc_id = self._get_free_account_id()

        # create account and add it to list
        new_acc = Account(config=self.config, callbacks=self.callbacks,
                          queue=self.queue, aid=acc_id)
        new_acc.type = acc_type
        new_acc.user = acc_user
        new_acc.password = acc_pass
        self.accounts[new_acc.aid] = new_acc

        # store updated accounts in file
        self.store()

        # log event
        log_msg = (f"account new: id {new_acc.aid} type {new_acc.type} "
                   f"user {new_acc.user}")
        logging.info(log_msg)

        # notify callback (if present) about new account
        await self.callbacks.call(Callback.ADD_ACCOUNT, new_acc, ())

        # return result
        result = Message.info(f"added account {new_acc.aid}.")
        if self.config.get_push_accounts():
            result += Message.account(new_acc)
        return result

    async def delete(self, acc_id: int) -> str:
        """
        Delete an account
        """

        # notify callback (if present) about deleted account
        acc = self.accounts[acc_id]
        await self.callbacks.call(Callback.DEL_ACCOUNT, acc, ())

        # remove account and update accounts file
        del self.accounts[acc_id]
        self.store()

        # log event
        log_msg = f"account deleted: id {acc_id}"
        logging.info(log_msg)

        return f"account {acc_id} deleted."
