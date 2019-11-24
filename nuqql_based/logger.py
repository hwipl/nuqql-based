"""
Nuqql-based logging
"""

import logging
import stat
import os

# TODO: move LOGLEVES to this file?
from nuqql_based.config import LOGLEVELS


LOGGERS = {}


def init_logger(config, name, file_name):
    """
    Create a logger with <name>, that logs to <file_name>
    """

    # determine logging level from config
    loglevel = LOGLEVELS[config["loglevel"]]

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)

    # create handler
    fileh = logging.FileHandler(file_name)
    fileh.setLevel(loglevel)

    # create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
        datefmt="%s")

    # add formatter to handler
    fileh.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(fileh)

    # return logger to caller
    return logger


def init_main_logger(config):
    """
    Initialize logger for main log
    """

    # make sure logs directory exists
    logs_dir = config["dir"] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(logs_dir, stat.S_IRWXU)

    # main log
    main_log = logs_dir / "main.log"
    LOGGERS["main"] = init_logger(config, "main", main_log)
    os.chmod(main_log, stat.S_IRUSR | stat.S_IWUSR)


def add_account_logger(conf, acc_id):
    """
    Add an account specific logger
    """

    # TODO: merge with init account loggers? remove init account loggers?
    # create new logger
    account_dir = conf["dir"] / "logs" / "account" / f"{acc_id}"
    account_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(account_dir, stat.S_IRWXU)
    account_log = account_dir / "account.log"
    # logger name must be string
    logger = init_logger(conf, str(acc_id), account_log)
    # TODO: do we still need LOGGERS[acc_id]?
    LOGGERS[acc_id] = logger
    os.chmod(account_log, stat.S_IRUSR | stat.S_IWUSR)

    return logger


def init_account_loggers(config, accounts):
    """
    Initialize loggers for account specific logs
    """

    # TODO: only init one account's logger and return it? let caller add it to
    # account?
    # make sure logs directory exists
    logs_dir = config["dir"] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(logs_dir, stat.S_IRWXU)

    # account logs
    account_dir = logs_dir / "account"
    account_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(account_dir, stat.S_IRWXU)
    for acc in accounts.keys():
        acc_dir = account_dir / f"{acc}"
        acc_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(acc_dir, stat.S_IRWXU)
        acc_log = acc_dir / "account.log"
        # logger name must be string
        accounts[acc].logger = init_logger(config, str(acc), acc_log)
        # TODO: do we still need LOGGERS[acc]?
        LOGGERS[acc] = accounts[acc].logger
        os.chmod(acc_log, stat.S_IRUSR | stat.S_IWUSR)


def get_logger(name):
    """
    Helper for getting the logger with the name <name>
    """

    return LOGGERS[name]
