"""
Nuqql-based configuration
"""

import configparser
import argparse
import logging
import pathlib
import stat
import os

from typing import Dict, TypedDict, Literal


class ConfigDict(TypedDict):
    """
    Type of config dictionary
    """

    af: str
    address: str
    port: int
    sockfile: pathlib.Path
    dir: pathlib.Path
    daemonize: bool
    loglevel: int


ConfigKey = Literal["af", "address", "port", "sockfile", "dir", "daemonize",
                    "loglevel"]


class Config:
    """
    Nuqql-based configuration
    """

    # logging levels
    _LOGLEVEL_MAP = {
        "debug":    logging.DEBUG,
        "info":     logging.INFO,
        "warn":     logging.WARNING,
        "error":    logging.ERROR
    }
    _DEFAULT_LOGLEVEL = "warn"

    def __init__(self, backend_name: str = "based"):
        # init config and define defaults
        self.config: ConfigDict = {
            "af": "inet",
            "address": "localhost",
            "port": 32000,
            "sockfile": pathlib.Path(f"{backend_name}.sock"),
            "dir": pathlib.Path.home() / f".config/nuqql-{backend_name}",
            "daemonize": False,
            "loglevel": self._LOGLEVEL_MAP[self._DEFAULT_LOGLEVEL],
        }

        # init from args and config file
        self._init()

    @staticmethod
    def get_from_args() -> Dict[str, str]:
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
                                                   "error"],
                            help="Logging level")

        # parse command line arguments and return result as dict
        args = parser.parse_args()
        return vars(args)

    def read_from_file(self) -> None:
        """
        Read configuration file into config
        """

        # make sure path and file exist
        self.config["dir"].mkdir(parents=True, exist_ok=True)
        os.chmod(self.config["dir"], stat.S_IRWXU)
        config_file = self.config["dir"] / "config.ini"
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
                    self.config["af"] = config[section].get(
                        "af", fallback=self.config["af"])
                    self.config["address"] = config[section].get(
                        "address", fallback=self.config["address"])
                    self.config["port"] = config[section].getint(
                        "port", fallback=self.config["port"])
                    self.config["sockfile"] = pathlib.Path(config[section].get(
                        "sockfile", fallback=str(self.config["sockfile"])))
                    self.config["dir"] = pathlib.Path(config[section].get(
                        "dir", fallback=str(self.config["dir"])))
                    self.config["daemonize"] = config[section].getboolean(
                        "daemonize", fallback=self.config["daemonize"])
                    self.config["loglevel"] = self._LOGLEVEL_MAP[
                        config[section].get(
                            "loglevel", fallback=self._DEFAULT_LOGLEVEL)]
                except ValueError as error:
                    error_msg = "Error parsing config file: {}".format(error)
                    print(error_msg)

        # make sure log level is correct
        if self.config["loglevel"] not in self._LOGLEVEL_MAP:
            self.config["loglevel"] = self._LOGLEVEL_MAP[
                self._DEFAULT_LOGLEVEL]
            error_msg = "Error parsing config file: wrong loglevel"
            print(error_msg)

    def _init(self) -> ConfigDict:
        """
        Initialize backend configuration from config file and
        command line parameters
        """

        # read command line arguments
        args = self.get_from_args()

        # read config file and load it into config
        if "dir" in args:
            self.config["dir"] = pathlib.Path(args["dir"])
        self.read_from_file()

        # overwrite config with command line arguments
        for key, value in args.items():
            if key in ("dir", "sockfile"):
                self.config[key] = pathlib.Path(value)
            else:
                self.config[key] = value

        return self.config

    def get(self, entry: ConfigKey = None):
        """
        Helper for getting the config or a single entry from the config
        """

        if entry:
            return self.config[entry]

        return self.config
