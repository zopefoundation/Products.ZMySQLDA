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
from _thread import get_ident

from .base import DB_CONN_STRING
from .base import NO_MYSQL_MSG
from .base import TABLE_COL_INT
from .base import TABLE_COL_VARCHAR
from .base import TABLE_NAME
from .base import MySQLRequiredLayer
from .base import PatchedConnectionTestsBase
from .base import have_test_database


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
                             use_unicode=True, auto_create_db=True, timeout=3)
        self.assertEqual(conn.getId(), 'conn_id')
        self.assertEqual(conn.title, 'Conn Title')
        self.assertEqual(conn.connection_string, 'db_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertIsNone(conn.charset)
        self.assertTrue(conn.auto_create_db)
        self.assertEqual(conn.timeout, 3)

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
                         use_unicode=True, auto_create_db=True, timeout=3)
        self.assertEqual(conn.title, 'New Title')
        self.assertEqual(conn.connection_string, 'new_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertTrue(conn.auto_create_db)
        self.assertIsNone(conn.charset)
        self.assertFalse(conn.connected())
        self.assertEqual(conn.timeout, 3)

        conn.manage_edit('Another Title', 'another_conn_string', check=True,
                         use_unicode=None, auto_create_db=None, charset='utf8',
                         timeout=20)
        self.assertEqual(conn.title, 'Another Title')
        self.assertEqual(conn.connection_string, 'another_conn_string')
        self.assertFalse(conn.use_unicode)
        self.assertEqual(conn.charset, 'utf8')
        self.assertFalse(conn.auto_create_db)
        self.assertTrue(conn.connected())
        self.assertEqual(conn.timeout, 20)

        Connection.connect = old_connect

    def test_zope_factory(self):
        from OFS.Folder import Folder

        from Products.ZMySQLDA.DA import manage_addZMySQLConnection

        container = Folder('root')
        manage_addZMySQLConnection(container, 'conn_id', 'Conn Title',
                                   'db_conn_string', False,
                                   use_unicode=True, charset='utf8',
                                   auto_create_db=True, timeout=15)
        conn = container.conn_id
        self.assertEqual(conn.getId(), 'conn_id')
        self.assertEqual(conn.title, 'Conn Title')
        self.assertEqual(conn.connection_string, 'db_conn_string')
        self.assertTrue(conn.use_unicode)
        self.assertEqual(conn.charset, 'utf8')
        self.assertTrue(conn.auto_create_db)
        self.assertEqual(conn.timeout, 15)

        # Make sure the defaults for use_unicode, auto_create_db and timeout
        # do the right thing
        manage_addZMySQLConnection(container, 'conn2', 'Other title',
                                   'db_conn_string', False)
        conn = container.conn2
        self.assertFalse(conn.use_unicode)
        self.assertIsNone(conn.charset)
        self.assertFalse(conn.auto_create_db)
        self.assertIsNone(conn.timeout)


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
        unencoded = 'foo'
        self.conn = self._makeOne('conn_id', 'Conn Title', 'db_conn_string',
                                  False, use_unicode=True)

        # The point of this test is not the quoting, which happens at
        # the MySQL library level, but the processing on our end, which
        # should return the same type of string.
        self.assertEqual(self.conn.sql_quote__(unencoded), unencoded)


@unittest.skipUnless(have_test_database(), NO_MYSQL_MSG)
class RealConnectionTests(unittest.TestCase):

    layer = MySQLRequiredLayer

    def _makeOne(self, use_unicode=False, charset=None, timeout=None):
        from Products.ZMySQLDA.DA import Connection
        return Connection('conn_id', 'Conn Title', DB_CONN_STRING, False,
                          use_unicode=use_unicode, charset=charset,
                          timeout=timeout)

    def _makeRequest(self):
        class DummyRequest(dict):
            pass

        class DummyResponse:
            def redirect(self, url):
                pass

        req = DummyRequest()
        req.RESPONSE = DummyResponse()
        return req

    def test_manage_edit_no_zmi_raises(self):
        conn = self._makeOne()
        self.assertRaises(Exception, conn.manage_edit,
                          'New Title', 'xyzinvalid zyxinvalid', check=True)

    def test_manage_edit_zmi_catches(self):
        # make sure connection issues in the ZMI don't cause blowups
        conn = self._makeOne()
        req = self._makeRequest()
        have_raised = ''
        try:
            conn.manage_edit('New Title', 'xyzinvalid zyxinvalid',
                             check=True, REQUEST=req)
        except Exception as e:
            have_raised = str(e)

        self.assertEqual(have_raised, '')

    def test_manage_test_ascii(self):
        self.da = self._makeOne(use_unicode=True)
        sql = "INSERT INTO %s VALUES (1, 'testing')" % TABLE_NAME
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], 'testing')

    def test_manage_test_no_use_unicode(self):
        # If no character set is specified and use_unicode is False,
        # mysqlclient uses utf8.
        self.da = self._makeOne(use_unicode=False)
        unicode_str = '\xfcbrigens'
        utf8_str = unicode_str.encode('utf8')
        sql = "INSERT INTO {} VALUES (1, '{}')".format(TABLE_NAME, unicode_str)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], utf8_str)

    def test_manage_test_use_unicode(self):
        # The connection is set up with ``use_unicode``, which means queries
        # will return unicode data.
        self.da = self._makeOne(use_unicode=True)
        unicode_str = '\xfcbrigens'
        sql = "INSERT INTO {} VALUES (1, '{}')".format(TABLE_NAME, unicode_str)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], unicode_str)

    def test_manage_test_utf8mb4_use_unicode(self):
        # The connection is set up with ``use_unicode``, which means queries
        # will return unicode data.
        self.da = self._makeOne(use_unicode=True, charset='utf8mb4')
        unicode_str = '\xfcbrigens'
        sql = "INSERT INTO {} VALUES (1, '{}')".format(TABLE_NAME, unicode_str)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], unicode_str)

    def test_manage_test_utf8_no_use_unicode(self):
        self.da = self._makeOne(use_unicode=False, charset='utf8')
        unicode_str = '\xfcbrigens'
        utf8_str = unicode_str.encode('utf8')
        sql = "INSERT INTO {} VALUES (1, '{}')".format(TABLE_NAME, unicode_str)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], utf8_str)

    def test_manage_test_utf8mb4_no_use_unicode(self):
        self.da = self._makeOne(use_unicode=False, charset='utf8mb4')
        unicode_str = '\xfcbrigens'
        utf8_str = unicode_str.encode('utf8')
        sql = "INSERT INTO {} VALUES (1, '{}')".format(TABLE_NAME, unicode_str)
        self.da.manage_test(sql)

        res = self.da.manage_test('SELECT * FROM %s' % TABLE_NAME)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][TABLE_COL_INT], 1)
        self.assertEqual(res[0][TABLE_COL_VARCHAR], utf8_str)

    def test_sql_quote___miss(self):
        TO_QUOTE = 'no quoting required'
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE), "'%s'" % TO_QUOTE)

    def test_sql_quote___embedded_apostrophe(self):
        TO_QUOTE = "w'embedded apostrophe"
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         "'w\\'embedded apostrophe'")

    def test_sql_quote___embedded_backslash(self):
        TO_QUOTE = 'embedded \\backslash'
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         "'embedded \\\\backslash'")

    def test_sql_quote___embedded_double_quote(self):
        # As it turns out, escaping double quotes will break
        # some servers, notably PostgreSQL, so we no longer do that.
        TO_QUOTE = 'embedded "double quote'
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         '\'embedded \\"double quote\'')

    def test_sql_quote___embedded_null(self):
        TO_QUOTE = "w'embedded apostrophe and \x00null"
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         "'w\\'embedded apostrophe and \\0null'")

        # This is another version of a nul character.
        TO_QUOTE = 'embedded other \x1anull'
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         "'embedded other \\Znull'")

    def test_sql_quote___embedded_carriage_return(self):
        TO_QUOTE = "w'embedded carriage\rreturn"
        conn = self._makeOne(use_unicode=True)
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         "'w\\'embedded carriage\\rreturn'")

    def test_sql_quote___miss_bytes(self):
        TO_QUOTE = b'no quoting required'
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE), b"'%s'" % TO_QUOTE)

    def test_sql_quote___embedded_apostrophe_bytes(self):
        TO_QUOTE = b"w'embedded apostrophe"
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b"'w\\'embedded apostrophe'")

    def test_sql_quote___embedded_backslash_bytes(self):
        TO_QUOTE = b'embedded \\backslash'
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b"'embedded \\\\backslash'")
        # Show for good measure that the seeming two backslashes
        # are really one, when you look at the raw string.
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         br"'embedded \\backslash'")

    def test_sql_quote___embedded_double_quote_bytes(self):
        # As it turns out, escaping double quotes will break
        # some servers, notably PostgreSQL, so we no longer do that.
        TO_QUOTE = b'embedded "double quote'
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b'\'embedded \\"double quote\'')

    def test_sql_quote___embedded_null_bytes(self):
        TO_QUOTE = b"w'embedded apostrophe and \x00null"
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b"'w\\'embedded apostrophe and \\0null'")

        # This is another version of a nul character.
        TO_QUOTE = b'embedded other \x1anull'
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b"'embedded other \\Znull'")

    def test_sql_quote___embedded_carriage_return_bytes(self):
        TO_QUOTE = b"w'embedded carriage\rreturn"
        conn = self._makeOne()
        self.assertEqual(conn.sql_quote__(TO_QUOTE),
                         b"'w\\'embedded carriage\\rreturn'")


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(ConnectionTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            PatchedConnectionTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(RealConnectionTests)))
