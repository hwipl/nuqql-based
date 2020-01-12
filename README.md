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

You can omit the callbacks you do not need in the callbacks list. In addition
to the code above, you need to implement the callbacks.


## Changes

* v0.1:
  * First release.
