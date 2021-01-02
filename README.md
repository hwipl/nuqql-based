# nuqql-based

nuqql-based is a basic network daemon library that implements the nuqql
interface. It can be used as a dummy backend for
[nuqql](https://github.com/hwipl/nuqql), e.g., for testing or as a basis for
the implementation of other nuqql backends.

Other backends using nuqql-based:
* [nuqql-slixmppd](https://github.com/hwipl/nuqql-slixmppd): a backend for the
  XMPP (Jabber) protocol
* [nuqql-matrixd](https://github.com/hwipl/nuqql-matrixd): a backend for the
  Matrix protocol
* [nuqql-matrixd-nio](https://github.com/hwipl/nuqql-matrixd-nio): a backend
  for the Matrix protocol

Dependencies:
* [daemon](https://pypi.org/project/python-daemon/) (optional): for daemonize
  support


## Setup

You can install nuqql-based, for example, with pip for your user only with the
following command:

```console
$ pip install --user nuqql-based
```

If you prefer to check out this repository with git and work with the
repository directly, you can install nuqql-based for your user in editable mode
with the following command:

```console
$ pip install --user -e .
```


## Usage

Creating a nuqql backend with the nuqql-based library consists of the steps in
the following boilerplate code:

```python
from nuqql_based.based import Based
from nuqql_based.callback import Callback

# create a new backend
BACKEND_NAME = "myBackend"
BACKEND_VERSION = "0.1"
based = Based(BACKEND_NAME, BACKEND_VERSION)

# set callbacks
callbacks = [
    # based events
    (Callback.BASED_CONFIG, based_config),
    (Callback.BASED_INTERRUPT, based_interrupt),
    (Callback.BASED_QUIT, based_quit),

    # nuqql messages
    (Callback.QUIT, stop),
    (Callback.ADD_ACCOUNT, add_account),
    (Callback.DEL_ACCOUNT, del_account),
    (Callback.SEND_MESSAGE, send_message),
    (Callback.SET_STATUS, set_status),
    (Callback.GET_STATUS, get_status),
    (Callback.CHAT_LIST, chat_list),
    (Callback.CHAT_JOIN, chat_join),
    (Callback.CHAT_PART, chat_part),
    (Callback.CHAT_SEND, chat_send),
    (Callback.CHAT_USERS, chat_users),
    (Callback.CHAT_INVITE, chat_invite),
]
based.set_callbacks(callbacks)
based.start()
```

You can omit the callbacks you do not need in the `callbacks` list. In addition
to the code above, you need to implement the callbacks you specify in your
`callbacks` list.

The parameters passed to all callbacks are: the account, the callback and a
callback-specific parameter tuple. The following example shows the
`send_message` callback:

```python
async def send_message(account, callback, params):
    """
    Send a message to another user.
    """

    dest, msg = params
    # do something with the message...

    return ""
```

The callbacks are only used for commands coming from nuqql. You must handle
backend-specific events like receiving messages from other users in your
backend code and optionally pass them to nuqql-based. The following example
shows how incoming messages from other users can be passed to nuqql-based with
`Message.message()` and `receive_msg()`:

```python
from nuqql_based.message import Message

def receive(account, timestamp, sender, destination, text):
    """
    Receive message from other user.
    """

    msg = Message.message(account, timestamp, sender, destination, text)
    account.receive_msg(msg)
```


## Changes

* v0.3.0:
  * Switch to asyncio and increase required Python version to >= 3.7
  * Remove copy of the buddy list from Account and rename callback
    `UPDATE_BUDDIES` to `GET_BUDDIES` to match new behaviour
  * Add callbacks:
    * `HELP_WELCOME`: welcome/help message for clients
    * `HELP_ACCOUNT_ADD`: help text for adding accounts
  * Add configuration option for filtering own messages
* v0.2.0:
  * Use only one log file
  * Add "push-accounts" to configuration/command line arguments
  * Add more info messages and extend output of "help" command
  * Change callback parameter from account id to Account
  * Add tests
  * Cleanups and fixes
* v0.1:
  * First release.
