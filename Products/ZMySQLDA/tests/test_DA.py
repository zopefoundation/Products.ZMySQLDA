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
""" Tests for the DA module
"""
import unittest

import six
from six.moves._thread import get_ident

from .base import _mySQLNotAvailable
from .base import DB_CONN_STRING
from .base import NO_MYSQL_MSG
from .base import TABLE_NAME
from .base import TABLE_COL_INT
from .base import TABLE_COL_VARCHAR
from .base import MySQLRequiredLayer
from .base import PatchedConnectionTestsBase


class ConnectionTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.ZMySQLDA.DA import Connection
        return Connection

    def _makeOne(self, *args, **kw):
        conn = self._getTargetClass()(*args, **kw)
        return conn

    def _simpleMakeOne(self):
        cls = self._getTargetClass()
        return cls('conn_id', 'Conn Title', 'db_conn_string', False)

    def test_initialization(self):
        conn = self._makeOne('conn_id', 'Conn Title', 'db_conn_string', False,
                             use_unicode=True, auto_create_db=True)
        self.assertEqual(conn.getId(), 'conn_id')
        self.assertEqual(conn.title, 'Conn Title')
        self.assertEqual(conn.connection_string, 'db_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertIsNone(conn.charset)
        self.assertTrue(conn.auto_create_db)

    def test_factory(self):
        from Products.ZMySQLDA.db import DB
        conn = self._simpleMakeOne()
        self.assertIs(conn.factory(), DB)

    def test__pool_key(self):
        conn = self._simpleMakeOne()
        self.assertEqual(conn._pool_key(), (conn.getId(),))

    def test_manage_edit(self):
        from Products.ZMySQLDA.DA import Connection
        old_connect = Connection.connect

        def fake_connect(self, conn_str):
            self._v_connected = True

        Connection.connect = fake_connect
        conn = self._simpleMakeOne()

        conn.manage_edit('New Title', 'new_conn_string', check=False,
                         use_unicode=True, auto_create_db=True)
        self.assertEqual(conn.title, 'New Title')
        self.assertEqual(conn.connection_string, 'new_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertTrue(conn.auto_create_db)
        self.assertIsNone(conn.charset)
        self.assertFalse(conn.connected())

        conn.manage_edit('Another Title', 'another_conn_string', check=True,
                         use_unicode=None, auto_create_db=None, charset='utf8')
        self.assertEqual(conn.title, 'Another Title')
        self.assertEqual(conn.connection_string, 'another_conn_string')
        self.assertFalse(conn.use_unicode)
        self.assertEqual(conn.charset, 'utf8')
        self.assertFalse(conn.auto_create_db)
        self.assertTrue(conn.connected())

        Connection.connect = old_connect

    def test_zope_factory(self):
        from OFS.Folder import Folder
        from Products.ZMySQLDA.DA import manage_addZMySQLConnection

        container = Folder('root')
        manage_addZMySQLConnection(container, 'conn_id', 'Conn Title',
                                   'db_conn_string', False,
                                   use_unicode=True, charset='utf8',
                                   auto_create_db=True)
        conn = container.conn_id
        self.assertEqual(conn.getId(), 'conn_id')
        self.assertEqual(conn.title, 'Conn Title')
        self.assertEqual(conn.connection_string, 'db_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertEqual(conn.charset, 'utf8')
        self.assertTrue(conn.auto_create_db)

        # Make sure the defaults for use_unicode and auto_create_db
        # do the right thing
        manage_addZMySQLConnection(container, 'conn2', 'Other title',
                                   'db_conn_string', False)
        conn = container.conn2
        self.assertFalse(conn.use_unicode)
        self.assertIsNone(conn.charset)
        self.assertFalse(conn.auto_create_db)


class PatchedConnectionTests(PatchedConnectionTestsBase):
    """ Tests that require faking out MySQLdb.connect
    """

    def _getTargetClass(self):
        from Products.ZMySQLDA.DA import Connection
        return Connection

    def _makeOne(self, *args, **kw):
        conn = self._getTargetClass()(*args, **kw)
        return conn

    def _simpleMakeOne(self):
        cls = self._getTargetClass()
        return cls('conn_id', 'Conn Title', 'db_conn_string', False)

    def test_connect(self):
        from DateTime.DateTime import DateTime
        from Products.ZMySQLDA.db import DBPool

        self.conn = self._simpleMakeOne()

        with self.assertRaises(AttributeError):
            self.conn._v_database_connection
        self.assertFalse(self.conn._v_connected)

        self.conn.connect(self.conn.connection_string)
        self.assertIsInstance(self.conn._v_database_connection, DBPool)
        self.assertIsInstance(self.conn._v_connected, DateTime)

    def test_tpValues(self):
        self.conn = self._simpleMakeOne()
        vals = self.conn.tpValues()
        self.assertEqual(vals[0].__name__, 'table1')
        self.assertEqual(vals[0].icon, 'table')

    def test_sql_quote__no_unicode(self):
        self.conn = self._simpleMakeOne()

        self.conn.sql_quote__('foo')

        db_pool = self.conn._v_database_connection._db_pool
        internal_conn = db_pool.get(get_ident()).db
        self.assertEqual(internal_conn.string_literal_called, 'foo')
        self.assertFalse(internal_conn.unicode_literal_called)

    def test_sql_quote__unicode(self):
        self.conn = self._makeOne('conn_id', 'Conn Title', 'db_conn_string',
                                  False, use_unicode=True)

        self.conn.sql_quote__(b'foo'.decode('ASCII'))

        db_pool = self.conn._v_database_connection._db_pool
        internal_conn = db_pool.get(get_ident()).db
        self.assertFalse(internal_conn.string_literal_called)
        self.assertEqual(internal_conn.unicode_literal_called,
                         b'foo'.decode('ASCII'))


@unittest.skipIf(_mySQLNotAvailable(), NO_MYSQL_MSG)
class RealConnectionTests(unittest.TestCase):

    layer = MySQLRequiredLayer

    def _makeOne(self, use_unicode=False, charset=None):
        from Products.ZMySQLDA.DA import Connection
        return Connection('conn_id', 'Conn Title', DB_CONN_STRING, False,
                          use_unicode=use_unicode, charset=charset)

    def test_manage_test_ascii(self):
        self.da = self._makeOne(use_unicode=True)
        sql = "INSERT INTO %s VALUES (1, 'testing')" % TABLE_NAME
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], 'testing')

    def test_manage_test_unicode(self):
        # The connection is set up with ``use_unicode``, which means queries
        # will return unicode data.
        self.da = self._makeOne(use_unicode=True)
        nonascii = u'\xfcbrigens'
        if six.PY3:
            sql = "INSERT INTO %s VALUES (1, '%s')" % (TABLE_NAME, nonascii)
        else:
            # Under Python 2 it is still necessary to INSERT with
            # an encoded string, unicode breaks here because the ``_mysql``
            # module will attempt to convert unicode to string with no
            # character set provided, which will then use ``ascii``.
            sql = "INSERT INTO %s VALUES (1, '%s')" % (TABLE_NAME,
                                                       nonascii.encode('UTF8'))
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], nonascii)

    def test_manage_test_encoded(self):
        # The connection is set up with ``use_unicode``, which means queries
        # will return unicode data.
        self.da = self._makeOne(use_unicode=False, charset='latin1')
        nonascii = u'\xfcbrigens'
        sql = "INSERT INTO %s VALUES (1, '%s')" % (TABLE_NAME,
                                                   nonascii.encode('latin1'))
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], nonascii.encode('latin1'))


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(ConnectionTests),
                               unittest.makeSuite(PatchedConnectionTests),
                               unittest.makeSuite(RealConnectionTests)))
