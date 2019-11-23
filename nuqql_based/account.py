"""
Nuqql-based accounts
"""

import configparser
import stat
import os

from nuqql_based.callback import Callback, callback
from nuqql_based.logger import LOGGERS
from nuqql_based.config import CONFIG


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
        self.buddies = []
        self.logger = None

    def send_msg(self, user, msg):
        """
        Send message to user. Currently, this only logs the message
        """

        # try to send message
        callback(self.aid, Callback.SEND_MESSAGE, (user, msg))

        # log message
        log_msg = "message: to {0}: {1}".format(user, msg)
        LOGGERS[self.aid].info(log_msg)


def store_accounts():
    """
    Store accounts in a file.
    """

    # set accounts file and init configparser
    accounts_file = CONFIG["dir"] / "accounts.ini"
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option

    # construct accounts config that will be written to the accounts file
    for acc in ACCOUNTS.values():
        section = "account {}".format(acc.aid)
        config[section] = {}
        config[section]["id"] = str(acc.aid)
        config[section]["type"] = acc.type
        config[section]["user"] = acc.user
        config[section]["password"] = acc.password

    try:
        with open(accounts_file, "w") as acc_file:
            # make sure only user can read/write file before storing anything
            os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

            # write accounts to file
            config.write(acc_file)
    except (OSError, configparser.Error) as error:
        error_msg = "Error storing accounts file: {}".format(error)
        LOGGERS["main"].error(error_msg)


def load_accounts():
    """
    Load accounts from a file.
    """

    # make sure path and file exist
    CONFIG["dir"].mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG["dir"], stat.S_IRWXU)
    accounts_file = CONFIG["dir"] / "accounts.ini"
    if not accounts_file.exists():
        return ACCOUNTS

    # make sure only user can read/write file before using it
    os.chmod(accounts_file, stat.S_IRUSR | stat.S_IWUSR)

    # read config file
    try:
        config = configparser.ConfigParser()
        config.read(accounts_file)
    except configparser.Error as error:
        error_msg = "Error loading accounts file: {}".format(error)
        LOGGERS["main"].error(error_msg)

    for section in config.sections():
        # try to read account from account file
        try:
            acc_id = int(config[section]["id"])
            acc_type = config[section]["type"]
            acc_user = config[section]["user"]
            acc_pass = config[section]["password"]
        except KeyError as error:
            error_msg = "Error loading account: {}".format(error)
            LOGGERS["main"].error(error_msg)
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
