"""
Nuqql-based accounts
"""

import configparser
import stat
import os

from nuqql_based.callback import Callback
from nuqql_based.buddy import Buddy
from nuqql_based import logger
from nuqql_based import config


ACCOUNTS = {}


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
        self.logger = None

    def send_msg(self, user, msg):
        """
        Send message to user.
        """

        # try to send message
        Callback.SEND_MESSAGE.call(self.aid, (user, msg))

        # log message
        log_msg = "message: to {0}: {1}".format(user, msg)
        log = logger.get_logger(self.aid)
        log.info(log_msg)

        # add unknown buddies on send
        self.add_buddy(user, "", "")

    def get_buddies(self):
        """
        Get the buddy list
        """

        return self._buddies

    def flush_buddies(self):
        """
        Flush buddy list
        """

        self._buddies = []

    def add_buddy(self, name, alias, status):
        """
        Add a buddy to the buddy list
        """

        for buddy in self._buddies:
            if buddy.name == name:
                return

        buddy = Buddy(name, alias, status)
        self._buddies.append(buddy)
        self.log("account {0}: new buddy: {1}".format(self.aid, name))

    def log(self, text):
        """
        Log text to account's logger if present
        """

        if self.logger:
            self.logger.info(text)


def store_accounts():
    """
    Store accounts in a file.
    """

    # set accounts file and init configparser
    conf = config.get_config()
    accounts_file = conf["dir"] / "accounts.ini"
    accconf = configparser.ConfigParser()
    accconf.optionxform = lambda option: option

    # construct accounts config that will be written to the accounts file
    for acc in ACCOUNTS.values():
        section = "account {}".format(acc.aid)
        accconf[section] = {}
        accconf[section]["id"] = str(acc.aid)
        accconf[section]["type"] = acc.type
        accconf[section]["user"] = acc.user
        accconf[section]["password"] = acc.password

    try:
        with open(accounts_file, "w") as acc_file:
            # make sure only user can read/write file before storing anything
            os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

            # write accounts to file
            accconf.write(acc_file)
    except (OSError, configparser.Error) as error:
        error_msg = "Error storing accounts file: {}".format(error)
        log = logger.get_logger("main")
        log.error(error_msg)


def load_accounts():
    """
    Load accounts from a file.
    """

    # make sure path and file exist
    conf = config.get_config()
    conf["dir"].mkdir(parents=True, exist_ok=True)
    os.chmod(conf["dir"], stat.S_IRWXU)
    accounts_file = conf["dir"] / "accounts.ini"
    if not accounts_file.exists():
        return ACCOUNTS

    # make sure only user can read/write file before using it
    os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

    # read config file
    try:
        accconf = configparser.ConfigParser()
        accconf.read(accounts_file)
    except configparser.Error as error:
        error_msg = "Error loading accounts file: {}".format(error)
        log = logger.get_logger("main")
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
            log = logger.get_logger("main")
            log.error(error_msg)
            continue

        # add account
        new_acc = Account(aid=acc_id, atype=acc_type, user=acc_user,
                          password=acc_pass)
        ACCOUNTS[new_acc.aid] = new_acc

    return ACCOUNTS


def get_accounts():
    """
    Helper for getting the accounts
    """

    return ACCOUNTS


def _get_free_account_id():
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


def add_account(acc_type, acc_user, acc_pass):
    """
    Add a new account
    """

    acc_id = _get_free_account_id()
    new_acc = Account(aid=acc_id, atype=acc_type, user=acc_user,
                      password=acc_pass)

    # make sure the account does not exist
    for acc in ACCOUNTS.values():
        if acc.type == new_acc.type and acc.user == new_acc.user:
            return "account already exists."

    # new account; add it
    ACCOUNTS[new_acc.aid] = new_acc

    # store updated accounts in file
    store_accounts()

    # create new logger
    conf = config.get_config()
    new_acc.logger = logger.add_account_logger(conf, acc_id)

    # log event
    log_msg = "account new: id {0} type {1} user {2}".format(new_acc.aid,
                                                             new_acc.type,
                                                             new_acc.user)
    log = logger.get_logger("main")
    log.info(log_msg)

    # notify callback (if present) about new account
    Callback.ADD_ACCOUNT.call(new_acc.aid, (new_acc, ))

    return "new account added."


def del_account(acc_id):
    """
    Delete an account
    """

    # remove account and update accounts file
    del ACCOUNTS[acc_id]
    store_accounts()

    # log event
    log_msg = "account deleted: id {0}".format(acc_id)
    log = logger.get_logger("main")
    log.info(log_msg)

    # notify callback (if present) about deleted account
    Callback.DEL_ACCOUNT.call(acc_id, ())

    return "account {} deleted.".format(acc_id)
