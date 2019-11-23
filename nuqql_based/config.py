"""
Nuqql-based configuration
"""

import configparser
import argparse
import logging
import pathlib
import stat
import os

# logging levels
LOGLEVELS = {
    "debug":    logging.DEBUG,
    "info":     logging.INFO,
    "warn":     logging.WARNING,
    "error":    logging.ERROR
}
DEFAULT_LOGLEVEL = "warn"


CONFIG = {}


def get_command_line_args():
    """
    Parse the command line and return command line arguments:
        af:         address family
        address:    AF_INET listen address
        port:       AF_INET listen port
        sockfile:   AF_UNIX listen socket file within working directory
        dir:        working directory
        daemonize:  daemonize process?
    """

    # init command line argument parser
    parser = argparse.ArgumentParser(description="Run nuqql backend.",
                                     argument_default=argparse.SUPPRESS)
    parser.add_argument("--af", choices=["inet", "unix"],
                        help="socket address family: \"inet\" for AF_INET, \
                        \"unix\" for AF_UNIX")
    parser.add_argument("--address", help="AF_INET listen address")
    parser.add_argument("--port", type=int, help="AF_INET listen port")
    parser.add_argument("--sockfile", help="AF_UNIX socket file in DIR")
    parser.add_argument("--dir", help="working directory")
    parser.add_argument("-d", "--daemonize", action="store_true",
                        help="daemonize process")
    parser.add_argument("--loglevel", choices=["debug", "info", "warn",
                                               "error"], help="Logging level")

    # parse command line arguments and return result as dict
    args = parser.parse_args()
    return vars(args)


def read_config_file():
    """
    Read configuration file into config
    """

    # make sure path and file exist
    CONFIG["dir"].mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG["dir"], stat.S_IRWXU)
    config_file = CONFIG["dir"] / "config.ini"
    if not config_file.exists():
        return

    # make sure only user can read/write file before using it
    os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)

    # read config file
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
    except configparser.Error as error:
        error_msg = "Error loading config file: {}".format(error)
        print(error_msg)

    for section in config.sections():
        # try to read config from config file
        if section == "config":
            try:
                CONFIG["af"] = config[section].get(
                    "af", fallback=CONFIG["af"])
                CONFIG["address"] = config[section].get(
                    "address", fallback=CONFIG["address"])
                CONFIG["port"] = config[section].getint(
                    "port", fallback=CONFIG["port"])
                CONFIG["sockfile"] = pathlib.Path(config[section].get(
                    "sockfile", fallback=CONFIG["sockfile"]))
                CONFIG["dir"] = pathlib.Path(config[section].get(
                    "dir", fallback=CONFIG["dir"]))
                CONFIG["daemonize"] = config[section].getboolean(
                    "daemonize", fallback=CONFIG["daemonize"])
                CONFIG["loglevel"] = config[section].get(
                    "loglevel", fallback=CONFIG["loglevel"])
            except ValueError as error:
                error_msg = "Error parsing config file: {}".format(error)
                print(error_msg)

    # make sure log level is correct
    if CONFIG["loglevel"] not in LOGLEVELS:
        CONFIG["loglevel"] = DEFAULT_LOGLEVEL
        error_msg = "Error parsing config file: wrong loglevel"
        print(error_msg)


def init_config(backend_name="based"):
    """
    Initialize backend configuration from config file and
    command line parameters
    """

    # define defaults
    CONFIG["af"] = "inet"
    CONFIG["address"] = "localhost"
    CONFIG["port"] = 32000
    CONFIG["sockfile"] = pathlib.Path(f"{backend_name}.sock")
    CONFIG["dir"] = pathlib.Path.home() / f".config/nuqql-{backend_name}"
    CONFIG["daemonize"] = False
    CONFIG["loglevel"] = DEFAULT_LOGLEVEL

    # read command line arguments
    args = get_command_line_args()

    # read config file and load it into config
    if "dir" in args:
        CONFIG["dir"] = pathlib.Path(args["dir"])
    read_config_file()

    # overwrite config with command line arguments
    for key, value in args.items():
        if key in ("dir", "sockfile"):
            CONFIG[key] = pathlib.Path(value)
        else:
            CONFIG[key] = value

    return CONFIG


def get_config():
    """
    Helper for getting the config
    """

    return CONFIG
