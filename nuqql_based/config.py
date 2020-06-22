"""
Nuqql-based configuration
"""

import configparser
import argparse
import logging
import pathlib
import stat
import os


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

    def __init__(self, backend_name: str, backend_version: str):
        # backend settings
        self._backend_name = backend_name
        self._backend_version = backend_version

        # init config and define defaults
        self._af = "inet"
        self._address = "localhost"
        self._port = 32000
        self._sockfile = pathlib.Path(f"{backend_name}.sock")
        self._dir = pathlib.Path.home() / f".config/nuqql-{backend_name}"
        self._daemonize = False
        self._loglevel = self._LOGLEVEL_MAP[self._DEFAULT_LOGLEVEL]
        self._history = True
        self._push_accounts = False

    def get_from_args(self) -> None:
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
        parser = argparse.ArgumentParser(description="Run nuqql backend.")
        parser.add_argument("--version", action="version",
                            version=self._backend_version)
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
        parser.add_argument("--disable-history", action="store_true",
                            help="disable message history")
        parser.add_argument("--push-accounts", action="store_true",
                            help="push accounts to client")

        # parse command line arguments
        args = parser.parse_args()

        # store args in config dictionary
        if args.af:
            self._af = args.af
        if args.address:
            self._address = args.address
        if args.port:
            self._port = args.port
        if args.sockfile:
            self._sockfile = pathlib.Path(args.sockfile)
        if args.dir:
            self._dir = pathlib.Path(args.dir)
        if args.daemonize:
            self._daemonize = args.daemonize
        if args.loglevel:
            self._loglevel = self._LOGLEVEL_MAP[args.loglevel]
        if args.disable_history:
            self._history = False
        if args.push_accounts:
            self._push_accounts = True

    def read_from_file(self) -> None:
        """
        Read configuration file into config
        """

        # make sure path and file exist
        self._dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self._dir, stat.S_IRWXU)
        config_file = self._dir / "config.ini"
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
                    self._af = config[section].get("af", fallback=self._af)
                    self._address = config[section].get(
                        "address", fallback=self._address)
                    self._port = config[section].getint(
                        "port", fallback=self._port)
                    self._sockfile = pathlib.Path(config[section].get(
                        "sockfile", fallback=str(self._sockfile)))
                    self._dir = pathlib.Path(config[section].get(
                        "dir", fallback=str(self._dir)))
                    self._daemonize = config[section].getboolean(
                        "daemonize", fallback=self._daemonize)
                    self._loglevel = self._LOGLEVEL_MAP.get(
                        config[section].get(
                            "loglevel", fallback=self._DEFAULT_LOGLEVEL),
                        self._LOGLEVEL_MAP[self._DEFAULT_LOGLEVEL])
                    self._history = config[section].getboolean(
                        "history", fallback=self._history)
                    self._push_accounts = config[section].getboolean(
                        "push-accounts", fallback=self._push_accounts)
                except ValueError as error:
                    error_msg = "Error parsing config file: {}".format(error)
                    print(error_msg)

    def init(self) -> None:
        """
        Initialize backend configuration from config file and
        command line parameters
        """

        # read command line arguments
        self.get_from_args()

        # read config file and load it into config
        self.read_from_file()

        # overwrite config with command line arguments
        self.get_from_args()

    def get_af(self) -> str:
        """
        Get the af entry from the config
        """

        return self._af

    def get_address(self) -> str:
        """
        Get the address entry from the config
        """

        return self._address

    def get_port(self) -> int:
        """
        Get the port entry from the config
        """

        return self._port

    def get_sockfile(self) -> pathlib.Path:
        """
        Get the sockfile entry from the config
        """

        return self._sockfile

    def get_dir(self) -> pathlib.Path:
        """
        Get the dir entry from the config
        """

        return self._dir

    def get_daemonize(self) -> bool:
        """
        Get the address entry from the config
        """

        return self._daemonize

    def get_loglevel(self) -> int:
        """
        Get the loglevel entry from the config
        """

        return self._loglevel

    def get_history(self) -> bool:
        """
        Get history entry from config: history enabled or disabled
        """

        return self._history

    def get_push_accounts(self) -> bool:
        """
        Get push accounts entry from config: pushing accounts to clients
        enabled or disabled
        """

        return self._push_accounts

    def get_name(self) -> str:
        """
        Get the name of the backend
        """

        return self._backend_name

    def get_version(self) -> str:
        """
        Get the version of the backend
        """

        return self._backend_version
