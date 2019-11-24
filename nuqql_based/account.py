"""
Nuqql-based accounts
"""

import configparser
import stat
import os

from nuqql_based.callback import Callback, callback
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
        log = logger.get_logger(self.aid)
        log.info(log_msg)


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
