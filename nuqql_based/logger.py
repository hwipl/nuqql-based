"""
Nuqql-based logging
"""

import logging
import stat
import os

from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:   # imports for typing
    import pathlib
    from nuqql_based.config import Config


class Loggers:
    """
    Loggers class
    """

    def __init__(self, config: "Config") -> None:
        self.config = config
        # TODO: add locking?
        self.loggers: Dict[str, logging.Logger] = {}

    def _init(self, name: str, file_name: "pathlib.Path") -> logging.Logger:
        """
        Create a logger with <name>, that logs to <file_name>
        """

        # determine logging level from config
        loglevel = self.config.get_loglevel()

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

    def init_main(self) -> None:
        """
        Initialize logger for main log
        """

        # make sure logs directory exists
        logs_dir = self.config.get_dir() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(logs_dir, stat.S_IRWXU)

        # main log
        main_log = logs_dir / "main.log"
        self.loggers["main"] = self._init("main", main_log)
        os.chmod(main_log, stat.S_IRUSR | stat.S_IWUSR)

    def add_account(self, acc_id: int) -> logging.Logger:
        """
        Add an account specific logger
        """

        # TODO: merge with init account loggers? remove init account loggers?
        # create new logger
        account_dir = self.config.get_dir() / "logs" / "account" / f"{acc_id}"
        account_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(account_dir, stat.S_IRWXU)
        account_log = account_dir / "account.log"
        # logger name must be string
        logger = self._init(str(acc_id), account_log)
        # TODO: do we still need LOGGERS[acc_id]?
        self.loggers[str(acc_id)] = logger
        os.chmod(account_log, stat.S_IRUSR | stat.S_IWUSR)

        return logger

    def get(self, name: str) -> logging.Logger:
        """
        Helper for getting the logger with the name <name>
        """

        return self.loggers[name]
