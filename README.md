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

If you prefer to checkout this repository with git and work with the repository
directly, you can install nuqql-based for your user in editable mode with the
following command:

```console
$ pip install --user -e .
```


## Changes

* v0.1:
  * First release.
