def manage_addZMySQLConnection(self, id, title,
                                connection_string,
                                check=None, REQUEST=None):
    """Add a MySQL connection to a folder.

    Arguments:

        REQUEST -- The current request

        title -- The title of the ZMySQLDA Connection (string)

        id -- The id of the ZMySQLDA Connection (string)

        connection_string -- The connection string is of the form:

                '[+/-]database[@host[:port]] [user [password [unix_socket]]]'

        or typically:

                'database user password'

        to use a MySQL server on localhost via the standard UNIX socket.
        Only specify host if the server is on a remote system. You can
        use a non-standard port, if necessary. If the UNIX socket is in
        a non-standard location, you can specify the full path to it
        after the password. Transactions will be used if the server
        supports them. If you are using non-transaction-safe tables,
        a '-' at the beginning will disable transactions. If you want to
        be sure transactions are used, a '+' at the beginning will
        forcibly enable transactions; an exception will be raised if
        the server does not support transactions.

    """

class Connection:
    """MySQL Connection Object"""

    __constructor__ = manage_addZMySQLConnection


