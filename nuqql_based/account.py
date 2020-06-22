"""
Nuqql-based accounts
"""

import configparser
import logging
import stat
import os

from threading import Lock
from typing import TYPE_CHECKING, List, Tuple, Dict

from nuqql_based.callback import Callback
from nuqql_based.message import Message
from nuqql_based.buddy import Buddy

if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from logging import Logger  # noqa
    from nuqql_based.callback import Callbacks  # noqa
    from nuqql_based.config import Config  # noqa


class Account:
    """
    Storage for account specific information
    """

    def __init__(self, config: "Config", callbacks: "Callbacks",
                 aid: int = 0) -> None:
        self.aid = aid
        self.name = ""
        self.type = "dummy"
        self.user = "dummy@dummy.com"
        self.password = "dummy_password"
        self.status = "online"
        self._buddies: List[Buddy] = []
        self._buddies_lock = Lock()
        self._messages: List[str] = []
        self._messages_lock = Lock()
        self._history: List[str] = []
        self._history_lock = Lock()
        self.config = config
        self.callbacks = callbacks

    def send_msg(self, user: str, msg: str) -> None:
        """
        Send message to user.
        """

        # try to send message
        if self.callbacks:
            self.callbacks.call(Callback.SEND_MESSAGE, self, (user, msg))

        # log message
        log_msg = "message: to {0}: {1}".format(user, msg)
        logging.info(log_msg)

        # add unknown buddies on send
        self.add_buddy(user, "", "")

    def receive_msg(self, msg: str) -> None:
        """
        Receive a message from other users or the backend
        """

        self._messages_lock.acquire()
        self._messages.append(msg)
        self._messages_lock.release()

        if Message.is_message(msg) and self.config.get_history():
            # TODO: add timestamp?
            self._history_lock.acquire()
            self._history.append(msg)
            self._history_lock.release()

    def get_messages(self) -> List[str]:
        """
        Get received messages as list
        """

        self._messages_lock.acquire()
        messages = self._messages[:]
        self._messages = []
        self._messages_lock.release()

        return messages

    def get_history(self) -> List[str]:
        """
        Get the message history
        """

        # TODO: add timestamp parameter?
        self._history_lock.acquire()
        history = self._history[:]
        self._history_lock.release()

        return history

    def get_buddies(self) -> List[Buddy]:
        """
        Get the buddy list
        """

        self._buddies_lock.acquire()
        buddies = self._buddies[:]
        self._buddies_lock.release()

        return buddies

    def _flush_buddies(self) -> None:
        self._buddies = []

    def flush_buddies(self) -> None:
        """
        Flush buddy list
        """

        self._buddies_lock.acquire()
        self._flush_buddies()
        self._buddies_lock.release()

    def _add_buddy(self, name: str, alias: str, status: str) -> bool:
        for buddy in self._buddies:
            if buddy.name == name:
                return False

        buddy = Buddy(name, alias, status)
        self._buddies.append(buddy)
        return True

    def add_buddy(self, name: str, alias: str, status: str) -> None:
        """
        Add a buddy to the buddy list
        """

        self._buddies_lock.acquire()
        was_new = self._add_buddy(name, alias, status)
        self._buddies_lock.release()
        if was_new:
            logging.info("account %d: new buddy: %s", self.aid, name)

    def update_buddies(self, buddy_list: List[Tuple[str, str, str]]) -> None:
        """
        Update buddy list with buddy_list (list of name, alias, status tuples)
        """

        self._buddies_lock.acquire()
        self._flush_buddies()
        for name, alias, status in buddy_list:
            self._add_buddy(name, alias, status)
        self._buddies_lock.release()


class AccountList:
    """
    List of all accounts
    """

    def __init__(self, config: "Config", callbacks: "Callbacks") -> None:
        self.config = config
        self.callbacks = callbacks
        # TODO: add locking?
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
            section = "account {}".format(acc.aid)
            accconf[section] = {}
            accconf[section]["id"] = str(acc.aid)
            accconf[section]["type"] = acc.type
            accconf[section]["user"] = acc.user
            accconf[section]["password"] = acc.password

        try:
            with open(accounts_file, "w") as acc_file:
                # make sure only user can read/write file before storing
                # anything
                os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

                # write accounts to file
                accconf.write(acc_file)
        except (OSError, configparser.Error) as error:
            error_msg = "Error storing accounts file: {}".format(error)
            logging.error(error_msg)

    def load(self) -> Dict[int, Account]:
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
            error_msg = "Error loading accounts file: {}".format(error)
            logging.error(error_msg)

        for section in accconf.sections():
            # try to read account from account file
            try:
                acc_id = int(accconf[section]["id"])
                acc_type = accconf[section]["type"]
                acc_user = accconf[section]["user"]
                acc_pass = accconf[section]["password"]
            except KeyError as error:
                error_msg = "Error loading account: {}".format(error)
                logging.error(error_msg)
                continue

            # add account
            self.add(acc_type, acc_user, acc_pass, acc_id=acc_id)

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

    def add(self, acc_type: str, acc_user: str, acc_pass: str,
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
                          aid=acc_id)
        new_acc.type = acc_type
        new_acc.user = acc_user
        new_acc.password = acc_pass
        self.accounts[new_acc.aid] = new_acc

        # store updated accounts in file
        self.store()

        # log event
        log_msg = "account new: id {0} type {1} user {2}".format(new_acc.aid,
                                                                 new_acc.type,
                                                                 new_acc.user)
        logging.info(log_msg)

        # notify callback (if present) about new account
        self.callbacks.call(Callback.ADD_ACCOUNT, new_acc, ())

        # return result
        result = Message.info("new account added.")
        if self.config.get_push_accounts():
            result += Message.account(new_acc)
        return result

    def delete(self, acc_id: int) -> str:
        """
        Delete an account
        """

        # notify callback (if present) about deleted account
        acc = self.accounts[acc_id]
        self.callbacks.call(Callback.DEL_ACCOUNT, acc, ())

        # remove account and update accounts file
        del self.accounts[acc_id]
        self.store()

        # log event
        log_msg = "account deleted: id {0}".format(acc_id)
        logging.info(log_msg)

        return "account {} deleted.".format(acc_id)
