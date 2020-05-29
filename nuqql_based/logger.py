"""
Nuqql-based logging
"""

import logging
import stat
import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # imports for typing
    # pylint: disable=cyclic-import
    from nuqql_based.config import Config  # noqa


def init(config: "Config") -> None:
    """
    Initialize logger
    """

    # make sure logs directory exists
    logs_dir = config.get_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(logs_dir, stat.S_IRWXU)

    # configure logging
    name = config.get_name()
    file_name = logs_dir / f"{name}.log"
    fmt = "%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"
    date_fmt = "%s"
    loglevel = config.get_loglevel()
    logging.basicConfig(filename=file_name, format=fmt, datefmt=date_fmt,
                        level=loglevel)

    # restrict log file access
    os.chmod(file_name, stat.S_IRUSR | stat.S_IWUSR)
