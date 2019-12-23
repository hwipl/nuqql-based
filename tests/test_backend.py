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

from nuqql_based.main import VERSION
from nuqql_based.message import Message


class BackendInetTest(unittest.TestCase):
    """
    Test the backend
    """

    def setUp(self) -> None:
        # create temporary directory
        self.test_dir = tempfile.mkdtemp()

        # start backend as subprocess
        path = Path(__file__).resolve().parents[1]
        backend_cmd = f"{path}/based.py --dir {self.test_dir} --af inet"
        self.proc = subprocess.Popen(backend_cmd, shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)

        # client connection
        self.buf = ""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self._connect()

    def _connect(self) -> None:
        """
        Network connection helper, tries to reach server for 5 seconds
        """
        tries = 0
        while tries < 50:
            try:
                self.sock.connect(("localhost", 32000))
                break
            except OSError:
                tries += 1
                time.sleep(0.1)

    def tearDown(self) -> None:
        # close socket
        self.sock.close()

        # close subprocess
        self.proc.terminate()
        self.proc.wait()

        # delete temporary directory
        shutil.rmtree(self.test_dir)

    def send_cmd(self, cmd: str) -> None:
        """
        Send a command to the backend
        """

        cmd = f"{cmd}\r\n"
        self.sock.send(cmd.encode())

    def recv_msg(self) -> str:
        """
        Receive a message from the backend
        """

        while self.buf.find("\r\n") == -1:
            data = self.sock.recv(1024)
            if not data:
                return ""
            self.buf += data.decode()

        eom = self.buf.find("\r\n")
        msg = self.buf[:eom]
        self.buf = self.buf[eom + 2:]

        return msg

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

    def test_account_list(self) -> None:
        """
        Test the account list command
        """

        # empty account list, except nothing/timeout
        self.send_cmd("account list")
        with self.assertRaises(socket.timeout):
            self.sock.settimeout(1)
            self.recv_msg()

        # add new account
        self.send_cmd("account add test test@example.com testpw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: new account added.")

        # retrieve account list again, should contain new account
        self.send_cmd("account list")
        reply = self.recv_msg()
        self.assertEqual(reply, "account: 0 () test test@example.com [online]")

        # add new account
        self.send_cmd("account add test test2@test.com test2pw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: new account added.")

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

        # delete first account
        self.send_cmd("account 0 delete")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: account 0 deleted.")

        # retrieve account list again, should only contain second account
        self.send_cmd("account list")
        reply = self.recv_msg()
        self.assertEqual(reply, "account: 1 () test test2@test.com [online]")

        # add another account, should get first account id
        self.send_cmd("account add test test3@other.com test3pw")
        reply = self.recv_msg()
        self.assertEqual(reply, "info: new account added.")

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


if __name__ == '__main__':
    unittest.main()
