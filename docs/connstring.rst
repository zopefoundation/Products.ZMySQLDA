.. _connection-string:

Connection Strings
------------------
The connection string used for Z MySQL Database Connection objects
are of the form::

   [*lock_name][+|-]database[@host[:port]] [user [password [unix_socket]]]

or typically just::

   database user password

to use a MySQL server on the local host via the standard UNIX socket.

The components are as follows:

  * ``*lock_name`` at the begining of the connection string leads to
    pseudo-transactional behavior. When the :term:`Zope` transaction begins, 
    a lock named after ``lock_name`` is acquired on the database server. When
    the :term:`Zope` transaction commits, the database lock will be released.
    If the :term:`Zope` transaction is aborted and restarted, which can happen
    due to ConflictErrors, you'll get an error in the logs, and
    inconsistent data. In this respect, it's equivalent to
    transactions turned off.

    Transactions are highly recommended. Using a named lock in
    conjunctions with transactions is probably pointless.

  * ``+`` or ``-``: Integrate database transactions with the :term:`Zope`
    transaction machinery. A ``-`` in front of the database tells ZMySQLDA
    to not use Zope's Transaction Manager, even if the server supports
    transactions. A ``+`` in front of the database tells ZMySQLDA
    that it must use transactions; an exception will be raised if
    they are not supported by the server. If neither ``-`` or ``+``
    are present, then transactions will be enabled if the server
    supports them.  If you are using non-transaction safe tables
    (TSTs) on a server that supports TSTs, use ``-``. If you require
    transactions, use ``+``. If you aren't sure, don't use either.

  * ``database``: The name of the database to connect to.

  * ``host``/``port``: Host and port where the database server listens.
    Only use this if the database server is on a remote system. To use a
    non-standard port on the local system, use 127.0.0.1 for the host instead
    of the hostname ``localhost``.

  * ``user``/``password``: Log into the database with the provided user
    and password.

  * ``unix_socket``: If the UNIX socket is in a non-standard location, you
    can specify the full path to it after the ``password``.
