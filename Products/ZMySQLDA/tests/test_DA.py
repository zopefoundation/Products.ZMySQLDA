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
import os
import unittest

import six
from six.moves._thread import get_ident

from .base import _mySQLNotAvailable
from .base import DB_CONN_STRING
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
        self.assertTrue(conn.auto_create_db)

    def test_factory(self):
        from Products.ZMySQLDA.db import DB
        conn = self._simpleMakeOne()
        self.assertIs(conn.factory(), DB)

    def test__pool_key(self):
        conn = self._simpleMakeOne()
        self.assertEqual(conn._pool_key(), (conn.getId(),))

    def test_manage_edit(self):
        conn = self._simpleMakeOne()
        conn.manage_edit('New Title', 'new_conn_string', check=False,
                         use_unicode=True, auto_create_db=True)
        self.assertEqual(conn.title, 'New Title')
        self.assertEqual(conn.connection_string, 'new_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertTrue(conn.auto_create_db)

    def test_zope_factory(self):
        from OFS.Folder import Folder
        from Products.ZMySQLDA.DA import manage_addZMySQLConnection

        container = Folder('root')
        manage_addZMySQLConnection(container, 'conn_id', 'Conn Title',
                                   'db_conn_string', False,
                                   use_unicode=True, auto_create_db=True)
        conn = container.conn_id
        self.assertEqual(conn.getId(), 'conn_id')
        self.assertEqual(conn.title, 'Conn Title')
        self.assertEqual(conn.connection_string, 'db_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertTrue(conn.auto_create_db)


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


skip_msg = 'Please see the documentation for running functional tests.'


@unittest.skipIf(_mySQLNotAvailable(), skip_msg)
class RealConnectionTests(unittest.TestCase):

    layer = MySQLRequiredLayer

    def _makeOne(self, *args, **kw):
        from Products.ZMySQLDA.DA import Connection
        return Connection('conn_id', 'Conn Title', DB_CONN_STRING, False)

    def test_manage_test_ascii(self):
        self.da = self._makeOne()
        sql = "INSERT INTO %s VALUES (1, 'testing')" % TABLE_NAME
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], 'testing')

    @unittest.skipIf('TRAVIS' in os.environ, 'Does not work on Travis CI')
    def test_manage_test_nonascii(self):
        self.da = self._makeOne()
        if six.PY3:
            nonascii = '\xfcbrigens'
            sql = "INSERT INTO %s VALUES (1, '%s')" % (TABLE_NAME, nonascii)
        else:
            nonascii = u'\xfcbrigens'.encode('UTF-8')
            sql = "INSERT INTO %s VALUES (1, '%s')" % (TABLE_NAME, nonascii)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], nonascii)


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(ConnectionTests),
                               unittest.makeSuite(PatchedConnectionTests),
                               unittest.makeSuite(RealConnectionTests)))
