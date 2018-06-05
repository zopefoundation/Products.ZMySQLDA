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
""" MySQL Database Connection
"""
import os

import six
from six.moves._thread import allocate_lock

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityInfo import ModuleSecurityInfo
from App.ImageFile import ImageFile
from App.special_dtml import HTMLFile
from Persistence import Persistent
from Shared.DC import ZRDB

from . import DABase
from .db import DBPool, DB
from .permissions import add_zmysql_database_connections


mod_security = ModuleSecurityInfo('Products.ZMySQLDA.DA')


mod_security.declareProtected(add_zmysql_database_connections,
                              'manage_addZMySQLConnectionForm')
manage_addZMySQLConnectionForm = HTMLFile("www/connectionAdd", globals())


mod_security.declareProtected(add_zmysql_database_connections,
                              'manage_addZMySQLConnection')
def manage_addZMySQLConnection(self, id, title, connection_string, check=None,
                               use_unicode=None, auto_create_db=None,
                               REQUEST=None):
    """Add a DB connection to a folder"""
    self._setObject(id,
                    Connection(id, title, connection_string, check,
                               use_unicode=use_unicode,
                               auto_create_db=auto_create_db))

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


# Connection Pool for connections to MySQL.
# Maps one mysql client connection to one DA object instance.
database_connection_pool_lock = allocate_lock()
database_connection_pool = {}

# Combining connection pool with the DB pool gets you
# one DA/connection per connection with 1 DBPool with 1 DB/thread
# pool_id -> DA -> DBPool -> thread id -> DB
# dc_pool[pool_id] == DBPool_instance
# DBPool_instance[thread id] == DB instance


class Connection(DABase.Connection):
    """ ZMySQL Database Adapter Connection.
    """

    database_type = 'MySQL'
    id = "%s_database_connection" % database_type
    meta_type = title = "Z %s Database Connection" % database_type
    security = ClassSecurityInfo()

    auto_create_db = True
    use_unicode = False
    _v_connected = ""

    manage_properties = HTMLFile("www/connectionEdit", globals())

    def __init__(self, id, title, connection_string, check, use_unicode=None,
                 auto_create_db=None):
        """ Instance setup. Optionally opens the connection (check arg).
        """
        if use_unicode is not None:
            self.use_unicode = bool(use_unicode)
        if auto_create_db is not None:
            self.auto_create_db = bool(auto_create_db)

        return DABase.Connection.__init__(self, id, title, connection_string,
                                          check)

    def __setstate__(self, state):
        """ Skip super's __setstate__ as it connects which we don't want
            due to pool_key depending on acquisition.
        """
        Persistent.__setstate__(self, state)

    def factory(self):
        """ Base API. Returns factory method for DB connections.
        """
        return DB

    def _pool_key(self):
        """ Return key used for DA pool.
        """
        return self.getPhysicalPath()

    def connect(self, s):
        """ Base API. Opens connection to mysql. Raises if problems.
        """
        pool_key = self._pool_key()
        connection = database_connection_pool.get(pool_key)

        if connection is not None and connection.connection == s:
            self._v_database_connection = connection
            self._v_connected = connection.connected_timestamp
        else:
            if connection is not None:
                connection.closeConnection()
            DB = self.factory()
            DB = DBPool(DB, create_db=self.auto_create_db,
                        use_unicode=self.use_unicode)
            database_connection_pool_lock.acquire()
            try:
                database_connection_pool[pool_key] = connection = DB(s)
            finally:
                database_connection_pool_lock.release()
            self._v_database_connection = connection
            # XXX If date is used as such, it can be wrong because an
            # existing connection may be reused. But this is suposedly
            # only used as a marker to know if connection was successfull.
            self._v_connected = connection.connected_timestamp

        return self  # ??? why doesn't this return the connection ???

    def sql_quote__(self, v, escapes={}):
        """ Base API. Used to message strings for use in queries.
        """
        try:
            connection = self._v_database_connection
        except AttributeError:
            self.connect(self.connection_string)
            connection = self._v_database_connection

        if self.use_unicode and isinstance(v, six.text_type):
            return connection.unicode_literal(v)
        else:
            return connection.string_literal(v)

    def manage_edit(self, title, connection_string, check=None,
                    use_unicode=None, auto_create_db=None):
        """ Zope management API.
        """
        if use_unicode is not None:
            self.use_unicode = bool(use_unicode)
        if auto_create_db is not None:
            self.auto_create_db = bool(auto_create_db)

        return DABase.Connection.manage_edit(self, title, connection_string,
                                             check=None)


InitializeClass(Connection)
mod_security.apply(globals())

misc_ = {}
for icon in (
    "table",
    "view",
    "stable",
    "what",
    "field",
    "text",
    "bin",
    "int",
    "float",
    "date",
    "time",
    "datetime",
):
    misc_[icon] = ImageFile(os.path.join("www", "%s.gif") % icon, globals())
