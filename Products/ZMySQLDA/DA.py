##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" The ZODB-based MySQL Database Connection object
"""
import six
from six.moves._thread import allocate_lock

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import change_database_methods
from AccessControl.Permissions import use_database_methods
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityInfo import ModuleSecurityInfo
from App.special_dtml import HTMLFile
from Persistence import Persistent
from Shared.DC.ZRDB.Connection import Connection as ConnectionBase

from .db import DB
from .db import DBPool
from .permissions import add_zmysql_database_connections
from .utils import TableBrowser
from .utils import table_icons

# Connection Pool for connections to MySQL.
# Maps one mysql client connection to one DA object instance.
database_connection_pool_lock = allocate_lock()
database_connection_pool = {}

# Combining connection pool with the DB pool gets you
# one DA/connection per connection with 1 DBPool with 1 DB/thread
# pool_id -> DA -> DBPool -> thread id -> DB
# dc_pool[pool_id] == DBPool_instance
# DBPool_instance[thread id] == DB instance


class Connection(ConnectionBase):
    """ Zope database adapter for MySQL/MariaDB
    """
    meta_type = "Z MySQL Database Connection"
    security = ClassSecurityInfo()
    zmi_icon = 'fas fa-database'

    auto_create_db = True
    use_unicode = False
    charset = None
    _v_connected = ""
    _isAnSQLConnection = 1
    info = None

    security.declareProtected(view_management_screens, 'manage_browse')
    manage_browse = HTMLFile("www/browse", globals())

    security.declareProtected(change_database_methods, 'manage_properties')
    manage_properties = HTMLFile("www/connectionEdit", globals())

    manage_options = ConnectionBase.manage_options + (
        {"label": "Browse", "action": "manage_browse"},)

    def __init__(self, id, title, connection_string, check, use_unicode=None,
                 charset=None, auto_create_db=None):
        """ Instance setup. Optionally opens the connection.

        :string: id -- The id of the ZMySQLDA Connection

        :string: title -- The title of the ZMySQLDA Connection

        :string: connection_string -- The connection string describes how to
                                      connect to the relational database.
                                      See the documentation for details.

        :bool: check -- Check if the database connection can be opened after
                        instantiation.

        :bool: use_unicode -- If set to ``True``, values from columns of type
                              ``CHAR``, ``VARCHAR`` and ``TEXT`` are returned
                              as unicode strings by the database backend.
                              Combined with the hardcoded ``utf8`` character
                              set of this package the setting allows you to
                              control the character set of database return
                              values better. Default: False.

        :string: charset -- The character set for the connection. MySQL/MariaDB
                            will encode query results to this character set.

                            On Python 2, both utf8 and Latin1 will work. On
                            Python 3, only utf8 will work.

                            Default on Python 2: Latin1 when ``use_unicode``
                            is off, utf8 otherwise
                            Default on Python 3: utf8

        :bool: auto_create_db -- If the database given in ``connection_string``
                                 does not exist, create it automatically.
                                 Default: False.
        """
        self.use_unicode = bool(use_unicode)
        self.charset = charset
        self.auto_create_db = bool(auto_create_db)
        return super(Connection, self).__init__(id, title, connection_string,
                                                check)

    def __setstate__(self, state):
        """ Skip super's __setstate__ as it connects which we don't want
            due to pool_key depending on acquisition.
        """
        Persistent.__setstate__(self, state)

    security.declareProtected(use_database_methods, 'factory')

    def factory(self):
        """ Base API. Returns factory method for DB connections.
        """
        return DB

    def _pool_key(self):
        """ Return key used for DA pool.
        """
        return self.getPhysicalPath()

    def _getConnection(self):
        """ Helper method to retrieve an existing or create a new connection
        """
        try:
            return self._v_database_connection
        except AttributeError:
            self.connect(self.connection_string)
            return self._v_database_connection

    security.declareProtected(use_database_methods, 'connect')

    def connect(self, conn_string):
        """ Base API. Opens connection to mysql. Raises if problems.

        :string: conn_string -- The database connection string
        """
        pool_key = self._pool_key()
        conn = database_connection_pool.get(pool_key)

        if conn is not None and conn.connection == conn_string:
            self._v_database_connection = conn
            self._v_connected = conn.connected_timestamp
        else:
            if conn is not None:
                conn.closeConnection()

            conn_pool = DBPool(self.factory(), create_db=self.auto_create_db,
                               use_unicode=self.use_unicode,
                               charset=self.charset)
            database_connection_pool_lock.acquire()
            try:
                conn = conn_pool(conn_string)
                database_connection_pool[pool_key] = conn
            finally:
                database_connection_pool_lock.release()

            self._v_database_connection = conn
            # XXX If date is used as such, it can be wrong because an
            # existing connection may be reused. But this is suposedly
            # only used as a marker to know if connection was successfull.
            self._v_connected = conn.connected_timestamp

        return self  # ??? why doesn't this return the connection ???

    security.declareProtected(use_database_methods, 'sql_quote__')

    def sql_quote__(self, sql_str, escapes={}):
        """ Base API. Used to massage SQL strings for use in queries.

        :string: sql_str -- The raw SQL string to transform.

        :dict: escapes -- Additional escape transformations.
                          Default: empty ``dict``.
        """
        connection = self._getConnection()

        if self.use_unicode and isinstance(sql_str, six.text_type):
            return connection.unicode_literal(sql_str)
        else:
            return connection.string_literal(sql_str)

    security.declareProtected(change_database_methods, 'manage_edit')

    def manage_edit(self, title, connection_string, check=None,
                    use_unicode=None, charset=None, auto_create_db=None,
                    REQUEST=None):
        """ Edit the connection attributes through the Zope ZMI.

        :string: title -- The title of the ZMySQLDA Connection

        :string: connection_string -- The connection string describes how to
                                      connect to the relational database.
                                      See the documentation for details.

        :bool: check -- Check if the database connection can be opened after
                        instantiation. Default: False.

        :bool: use_unicode -- Use unicode internally. Default: False.

        :string: charset -- The character set for the connection. MySQL/MariaDB
                            will encode query results to this character set.

                            On Python 2, both utf8 and Latin1 will work. On
                            Python 3, only utf8 will work.

                            Default on Python 2: Latin1 when ``use_unicode``
                            is off, utf8 otherwise
                            Default on Python 3: utf8

        :bool: auto_create_db -- If the database given in ``connection_string``
                                 does not exist, create it automatically.
                                 Default: False.

        :request: REQUEST -- A Zope REQUEST object
        """
        self.use_unicode = bool(use_unicode)
        self.charset = charset
        self.auto_create_db = bool(auto_create_db)

        try:
            result = super(Connection, self).manage_edit(title,
                                                         connection_string,
                                                         check=check)
            msg = 'Changes applied.'
        except Exception as exc:
            msg = 'ERROR: %s' % str(exc)
            if REQUEST is None:
                raise

        if REQUEST is None:
            return result
        else:
            url = '%s/manage_properties?manage_tabs_message=%s'
            REQUEST.RESPONSE.redirect(url % (self.absolute_url(), msg))

    security.declareProtected(view_management_screens, 'tpValues')

    def tpValues(self):
        """ Support the DTML ``tree`` tag

        Used in the Zope ZMI ``Browse`` tab
        """
        t_list = []
        connection = self._getConnection()

        for t_info in connection.tables(rdb=0):
            try:
                t_browser = TableBrowser()
                t_browser.__name__ = t_info["table_name"]
                t_browser._d = t_info
                t_browser._c = connection
                t_browser.icon = table_icons.get(t_info["table_type"], "text")
                t_list.append(t_browser)
            except Exception:
                pass

        return t_list


InitializeClass(Connection)


mod_security = ModuleSecurityInfo('Products.ZMySQLDA.DA')
mod_security.declareProtected(add_zmysql_database_connections,
                              'manage_addZMySQLConnectionForm')
manage_addZMySQLConnectionForm = HTMLFile("www/connectionAdd", globals())

mod_security.declareProtected(add_zmysql_database_connections,
                              'manage_addZMySQLConnection')


def manage_addZMySQLConnection(self, id, title, connection_string, check=None,
                               use_unicode=None, auto_create_db=None,
                               charset=None, REQUEST=None):
    """Factory function to add a connection object from the Zope ZMI.

    :string: id -- The id of the ZMySQLDA Connection

    :string: title -- The title of the ZMySQLDA Connection

    :string: connection_string -- The connection string describes how to
                                  connect to the relational database.
                                  See the documentation for details.

    :bool: check -- Check if the database connection can be opened after
                    instantiation. Default: False.

    :bool: use_unicode -- If set to ``True``, values from columns of type
                          ``CHAR``, ``VARCHAR`` and ``TEXT`` are returned
                          as unicode strings by the database backend.
                          Combined with the hardcoded ``utf8`` character
                          set of this package the setting allows you to
                          control the character set of database return values
                          better. Default: False.

    :string: charset -- The character set for the connection. MySQL/MariaDB
                        will encode query results to this character set.

                        On Python 2, both utf8 and Latin1 will work. On
                        Python 3, only utf8 will work.

                        Default on Python 2: Latin1 when ``use_unicode``
                        is off, utf8 otherwise
                        Default on Python 3: utf8

    :bool: auto_create_db -- If the database given in ``connection_string``
                             does not exist, create it automatically.
                             Default: False.

    :object: REQUEST -- The currently active Zope request object.
                        Default: None.
    """
    self._setObject(id,
                    Connection(id, title, connection_string, check,
                               use_unicode=use_unicode, charset=charset,
                               auto_create_db=auto_create_db))

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


mod_security.apply(globals())
