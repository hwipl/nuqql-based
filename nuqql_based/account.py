"""
Nuqql-based accounts
"""

import configparser
import stat
import os

from threading import Lock

from nuqql_based.callback import Callback
from nuqql_based.message import Message
from nuqql_based.buddy import Buddy


class Account:
    """
    Storage for account specific information
    """

    def __init__(self, aid=0, name="", atype="dummy", user="dummy@dummy.com",
                 password="dummy_password", status="online"):
        self.aid = aid
        self.name = name
        self.type = atype
        self.user = user
        self.password = password
        self.status = status
        self._buddies = []
        self._buddies_lock = Lock()
        self._messages = []
        self._messages_lock = Lock()
        self._history = []
        self._history_lock = Lock()
        self.logger = None
        self.callbacks = None

    def send_msg(self, user, msg):
        """
        Send message to user.
        """

        # try to send message
        self.callbacks.call(Callback.SEND_MESSAGE, self.aid, (user, msg))

        # log message
        log_msg = "message: to {0}: {1}".format(user, msg)
        self.logger.info(log_msg)

        # add unknown buddies on send
        self.add_buddy(user, "", "")

    def receive_msg(self, msg):
        """
        Receive a message from other users or the backend
        """

        self._messages_lock.acquire()
        self._messages.append(msg)
        self._messages_lock.release()

        if Message.is_message(msg):
            # TODO: add configuration parameter if history is wanted?
            # TODO: add timestamp?
            self._history_lock.acquire()
            self._history.append(msg)
            self._history_lock.release()

    def get_messages(self):
        """
        Get received messages as list
        """

        self._messages_lock.acquire()
        messages = self._messages[:]
        self._messages = []
        self._messages_lock.release()

        return messages

    def get_history(self):
        """
        Get the message history
        """

        # TODO: add timestamp parameter?
        self._history_lock.acquire()
        history = self._history[:]
        self._history_lock.release()

        return history

    def get_buddies(self):
        """
        Get the buddy list
        """

        self._buddies_lock.acquire()
        buddies = self._buddies[:]
        self._buddies_lock.release()

        return buddies

    def _flush_buddies(self):
        self._buddies = []

    def flush_buddies(self):
        """
        Flush buddy list
        """

        self._buddies_lock.acquire()
        self._flush_buddies()
        self._buddies_lock.release()

    def _add_buddy(self, name, alias, status):
        for buddy in self._buddies:
            if buddy.name == name:
                return False

        buddy = Buddy(name, alias, status)
        self._buddies.append(buddy)
        return True

    def add_buddy(self, name, alias, status):
        """
        Add a buddy to the buddy list
        """

        self._buddies_lock.acquire()
        was_new = self._add_buddy(name, alias, status)
        self._buddies_lock.release()
        if was_new:
            self.log("account {0}: new buddy: {1}".format(self.aid, name))

    def update_buddies(self, buddy_list):
        """
        Update buddy list with buddy_list (list of name, alias, status tuples)
        """

        self._buddies_lock.acquire()
        self._flush_buddies()
        for name, alias, status in buddy_list:
            self._add_buddy(name, alias, status)
        self._buddies_lock.release()

    def log(self, text):
        """
        Log text to account's logger if present
        """

        if self.logger:
            self.logger.info(text)


class AccountList:
    """
    List of all accounts
    """

    def __init__(self, config, loggers, callbacks):
        self.config = config
        self.loggers = loggers
        self.callbacks = callbacks
        # TODO: add locking?
        self.accounts = {}

    def store(self):
        """
        Store accounts in a file.
        """

        # set accounts file and init configparser
        accounts_file = self.config.get("dir") / "accounts.ini"
        accconf = configparser.ConfigParser()
        accconf.optionxform = lambda option: option

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
            log = self.loggers.get("main")
            log.error(error_msg)

    def load(self):
        """
        Load accounts from a file.
        """

        # make sure path and file exist
        self.config.get("dir").mkdir(parents=True, exist_ok=True)
        os.chmod(self.config.get("dir"), stat.S_IRWXU)
        accounts_file = self.config.get("dir") / "accounts.ini"
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
            log = self.loggers.get("main")
            log.error(error_msg)

        for section in accconf.sections():
            # try to read account from account file
            try:
                acc_id = int(accconf[section]["id"])
                acc_type = accconf[section]["type"]
                acc_user = accconf[section]["user"]
                acc_pass = accconf[section]["password"]
            except KeyError as error:
                error_msg = "Error loading account: {}".format(error)
                log = self.loggers.get("main")
                log.error(error_msg)
                continue

            # add account
            self.add(acc_type, acc_user, acc_pass, acc_id=acc_id)

        return self.accounts

    def get(self):
        """
        Helper for getting the accounts
        """

        return self.accounts

    def _get_free_account_id(self):
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

    def add(self, acc_type, acc_user, acc_pass, acc_id=None):
        """
        Add a new account
        """

        if acc_id is None:
            acc_id = self._get_free_account_id()
        new_acc = Account(aid=acc_id, atype=acc_type, user=acc_user,
                          password=acc_pass)
        new_acc.callbacks = self.callbacks

        # make sure the account does not exist
        for acc in self.accounts.values():
            if acc.type == new_acc.type and acc.user == new_acc.user:
                return "account already exists."

        # new account; add it
        self.accounts[new_acc.aid] = new_acc

        # store updated accounts in file
        self.store()

        # create new logger
        new_acc.logger = self.loggers.add_account(acc_id)

        # log event
        log_msg = "account new: id {0} type {1} user {2}".format(new_acc.aid,
                                                                 new_acc.type,
                                                                 new_acc.user)
        log = self.loggers.get("main")
        log.info(log_msg)

        # notify callback (if present) about new account
        self.callbacks.call(Callback.ADD_ACCOUNT, new_acc.aid, (new_acc, ))

        return "new account added."

    def delete(self, acc_id):
        """
        Delete an account
        """

        # remove account and update accounts file
        del self.accounts[acc_id]
        self.store()

        # log event
        log_msg = "account deleted: id {0}".format(acc_id)
        log = self.loggers.get("main")
        log.info(log_msg)

        # notify callback (if present) about deleted account
        self.callbacks.call(Callback.DEL_ACCOUNT, acc_id, ())

        return "account {} deleted.".format(acc_id)
