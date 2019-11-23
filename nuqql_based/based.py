#!/usr/bin/env python3

"""
Basic nuqql backend
"""

import html
import sys

from nuqql_based.account import ACCOUNTS, load_accounts
from nuqql_based.logger import init_main_logger, init_account_loggers
from nuqql_based.config import init_config
from nuqql_based.message import Format
from nuqql_based.server import run_server


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
