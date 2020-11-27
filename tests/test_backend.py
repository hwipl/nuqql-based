"""
Backend testing code
"""

import subprocess
import unittest
import tempfile
import shutil
import socket
import time

from pathlib import Path
from typing import Any, Optional

from nuqql_based.main import VERSION
from nuqql_based.message import Message

# default socket timeout
DEFAULT_TIMEOUT = 10


class BackendInetTest(unittest.TestCase):
    """
    Test the backend with an AF_INET socket
    """

    # test run counter
    test_run = 0

    def setUp(self) -> None:
        # increase test run counter
        self.__class__.test_run += 1

        # create temporary directory
        self.test_dir = tempfile.mkdtemp()

        # start backend as subprocess
        self.path = Path(__file__).resolve().parents[1]
        self.backend_cmd = ""
        self._set_backend_cmd()
        self.proc: Optional[subprocess.Popen] = None
        self.proc = subprocess.Popen(self.backend_cmd, shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)

        # client connection
        self.buf = ""
        self.sock: Optional[socket.socket] = None
        self._set_socket()
        self.set_timeout(DEFAULT_TIMEOUT)
        self.server_addr: Any = None
        self._set_server_addr()
        self._connect()

    def _set_backend_cmd(self) -> None:
        """
        Set the backend command
        """

        port = 32000 + self.test_run
        self.backend_cmd = f"{self.path}/based.py --dir {self.test_dir} " \
            f"--af inet --port {port}"

    def _set_socket(self) -> None:
        """
        Set the client socket
        """

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _set_server_addr(self) -> None:
        """
        Set the server address
        """

        self.server_addr = ("localhost", 32000 + self.test_run)

    def _connect(self) -> None:
        """
        Network connection helper, tries to reach server for 5 seconds
        """

        assert self.sock
        tries = 0
        while tries < 50:
            try:
                time.sleep(1)
                self.sock.connect(self.server_addr)
                break
            except OSError:
                tries += 1

    def tearDown(self) -> None:
        assert self.sock and self.proc

        # close socket
        self.sock.close()
        self.sock = None

        # close subprocess
        self.proc.terminate()
        self.proc.wait()
        self.proc = None

        # delete temporary directory
        shutil.rmtree(self.test_dir)

    def send_cmd(self, cmd: str) -> None:
        """
        Send a command to the backend
        """

        assert self.sock
        cmd = f"{cmd}\r\n"
        self.sock.sendall(cmd.encode())

    def recv_msg(self) -> str:
        """
        Receive a message from the backend
        """

        assert self.sock
        while self.buf.find("\r\n") == -1:
            data = self.sock.recv(1024)
            if not data:
                return ""
            self.buf += data.decode()

        eom = self.buf.find("\r\n")
        msg = self.buf[:eom]
        self.buf = self.buf[eom + 2:]

        return msg

    def set_timeout(self, timeout: Optional[float]) -> None:
        """
        Set socket timeout
        """

        assert self.sock
        self.sock.settimeout(timeout)

    def test_version(self) -> None:
        """
        Test the version command
        """

        self.send_cmd("version")
        reply = self.recv_msg()
        self.assertEqual(reply, f"info: version: based v{VERSION}")

    def test_help(self) -> None:
        """
        Test the help command
        """

        self.send_cmd("help")
        reply = self.recv_msg()
        self.assertEqual(reply, str(Message.HELP_MSG)[:-2])

    def test_bye(self) -> None:
        """
        Test the bye command
        """

        self.send_cmd("bye")
        reply = self.recv_msg()
        self.assertEqual(reply, "")

    def test_quit(self) -> None:
        """
        Test the bye command
        """

        self.send_cmd("quit")
        reply = self.recv_msg()
        self.assertEqual(reply, "")

    def test_accounts(self) -> None:
        """
        Test account listing as well as adding and deleting of accounts
        """

        # empty account list, except nothing/timeout
        self.send_cmd("account list")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: listed accounts.")

        # add new account
        self.send_cmd("account add test test@example.com testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # retrieve account list again, should contain new account
        self.send_cmd("account list")
        reply = self.recv_msg()
        self.assertEqual(reply, "account: 0 () test test@example.com [online]")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: listed accounts.")

        # add new account
        self.send_cmd("account add test test2@test.com test2pw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 1.")

        # retrieve account list again, should contain new account
        self.send_cmd("account list")
        replies = []
        replies.append(self.recv_msg())
        replies.append(self.recv_msg())
        replies.sort()
        self.assertEqual(replies[0],
                         "account: 0 () test test@example.com [online]")
        self.assertEqual(replies[1],
                         "account: 1 () test test2@test.com [online]")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: listed accounts.")

        # delete first account
        self.send_cmd("account 0 delete")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: account 0 deleted.")

        # retrieve account list again, should only contain second account
        self.send_cmd("account list")
        reply = self.recv_msg()
        self.assertEqual(reply, "account: 1 () test test2@test.com [online]")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: listed accounts.")

        # add another account, should get first account id
        self.send_cmd("account add test test3@other.com test3pw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # retrieve account list again, should contain new account
        self.send_cmd("account list")
        replies = []
        replies.append(self.recv_msg())
        replies.append(self.recv_msg())
        replies.sort()
        self.assertEqual(replies[0],
                         "account: 0 () test test3@other.com [online]")
        self.assertEqual(replies[1],
                         "account: 1 () test test2@test.com [online]")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: listed accounts.")

    def test_buddies(self) -> None:
        """
        Test retrieving the buddy list and buddies adding with send
        """

        # retrieve buddy list with no accounts
        self.send_cmd("account 0 buddies")
        reply = self.recv_msg()
        self.assertEqual(reply, "error: invalid account")

        # add an account
        self.send_cmd("account add test test@example.com testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # retrieve buddy list with empty buddy list
        self.send_cmd("account 0 buddies")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: got buddies for account 0.")

        # add buddy with send and retrieve buddy list
        self.send_cmd("account 0 send buddy1@example.com test")
        reply = self.recv_msg()
        self.assertEqual(reply[:8], "message:")  # test backend returns msg
        self.send_cmd("account 0 buddies")
        reply = self.recv_msg()
        self.assertEqual(reply,
                         "buddy: 0 status:  name: buddy1@example.com alias: ")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: got buddies for account 0.")

        # add more buddies and retrieve buddy list again
        self.send_cmd("account 0 send buddy2@test.com test")
        reply = self.recv_msg()
        self.assertEqual(reply[:8], "message:")  # test backend returns msg
        self.send_cmd("account 0 send buddy3@other.com test")
        reply = self.recv_msg()
        self.assertEqual(reply[:8], "message:")  # test backend returns msg
        self.send_cmd("account 0 buddies")
        replies = []
        replies.append(self.recv_msg())
        replies.append(self.recv_msg())
        replies.append(self.recv_msg())
        replies.sort()
        self.assertEqual(replies[0],
                         "buddy: 0 status:  name: buddy1@example.com alias: ")
        self.assertEqual(replies[1],
                         "buddy: 0 status:  name: buddy2@test.com alias: ")
        self.assertEqual(replies[2],
                         "buddy: 0 status:  name: buddy3@other.com alias: ")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: got buddies for account 0.")

        # retrieve only online buddies
        self.send_cmd("account 0 buddies online")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: got buddies for account 0.")

    def test_send(self) -> None:
        """
        Test sending messages
        """

        # try without an account
        buddy = "buddy1@example.com"
        self.send_cmd(f"account 0 send {buddy} this is a test!")
        reply = self.recv_msg()
        self.assertEqual(reply, "error: invalid account")

        # add an account
        user = "test@example.com"
        self.send_cmd(f"account add test {user} testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # try again, there should be no reply
        msg = "this is a test!"
        self.send_cmd(f"account 0 send {buddy} {msg}")
        reply = self.recv_msg()
        self.assertRegex(reply,
                         f"message: 0 {user} [0-9]+ {buddy} {msg.upper()}")

    def test_collect(self) -> None:
        """
        Test collecting old messages from history
        """

        # try without an account
        self.send_cmd("account 0 collect")
        reply = self.recv_msg()
        self.assertEqual(reply, "error: invalid account")

        # add an account
        self.send_cmd("account add test test@example.com testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # try again, there should be no reply because history is empty
        self.send_cmd("account 0 collect")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: collected messages for account 0.")

    def test_status(self) -> None:
        """
        Test getting and setting the status
        """

        # try without an account
        self.send_cmd("account 0 status get")
        reply = self.recv_msg()
        self.assertEqual(reply, "error: invalid account")
        self.send_cmd("account 0 status set away")
        reply = self.recv_msg()
        self.assertEqual(reply, "error: invalid account")

        # add an account
        self.send_cmd("account add test test@example.com testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: added account 0.")

        # get status again
        self.send_cmd("account 0 status get")
        reply = self.recv_msg()
        self.assertEqual(reply, "status: account 0 status: online")

        # set status to away
        self.send_cmd("account 0 status set away")
        reply = self.recv_msg()
        self.assertEqual(reply, "status: account 0 status: away")

        # get status again
        self.send_cmd("account 0 status get")
        reply = self.recv_msg()
        self.assertEqual(reply, "status: account 0 status: away")


class BackendUnixTest(BackendInetTest):
    """
    Test the backend with an AF_UNIX socket
    """

    def _set_backend_cmd(self) -> None:
        """
        Get the backend command
        """

        self.backend_cmd = f"{self.path}/based.py --dir {self.test_dir} "\
            f"--af unix"

    def _set_socket(self) -> None:
        """
        Get the client socket
        """

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def _set_server_addr(self) -> None:
        """
        Get the server address
        """

        self.server_addr = str(Path(self.test_dir) / "based.sock")


if __name__ == '__main__':
    unittest.main()
