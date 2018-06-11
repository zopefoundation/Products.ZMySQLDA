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
""" Tests for the db module
"""
import unittest

from six.moves._thread import get_ident

from .base import PatchedConnectionTestsBase
from .dummy import FakeConnection


class DbFunctionsTests(unittest.TestCase):

    def test_DateTime_or_None(self):
        from DateTime.DateTime import DateTime
        from Products.ZMySQLDA.db import DateTime_or_None

        self.assertIsInstance(DateTime_or_None(None), DateTime)
        self.assertIsInstance(DateTime_or_None(DateTime()), DateTime)
        self.assertIsInstance(DateTime_or_None('1970-01-01 00:00:00'),
                              DateTime)
        self.assertIsNone(DateTime_or_None(''))


class DBPoolTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.ZMySQLDA.db import DBPool
        from Products.ZMySQLDA.db import DB
        return DBPool(DB, **kw)

    def test_instantiate_defaults(self):
        from Products.ZMySQLDA.db import DB
        pool = self._makeOne()

        self.assertIs(pool._db_cls, DB)
        self.assertEqual(pool._db_pool, {})
        self.assertFalse(pool._create_db)
        self.assertFalse(pool.use_unicode)

    def test_instantiate(self):
        pool = self._makeOne(create_db=True, use_unicode=True)

        self.assertTrue(pool._create_db)
        self.assertTrue(pool.use_unicode)

    def test_closeConnection(self):
        pool = self._makeOne()

        pool._db_pool[get_ident()] = 'foo'
        self.assertEqual(pool._db_pool, {get_ident(): 'foo'})
        pool.closeConnection()
        self.assertEqual(pool._db_pool, {})

        # This should not raise an error
        pool.closeConnection()

    def test_close(self):
        pool = self._makeOne()

        pool._db_pool['foo'] = 1
        pool._db_pool['bar'] = 2
        self.assertDictEqual(pool._db_pool, {'foo': 1, 'bar': 2})
        pool.close()
        self.assertEqual(pool._db_pool, {})

    def test__pool_get_set_del(self):
        pool = self._makeOne()

        self.assertIsNone(pool._pool_get('foo'))
        pool._pool_set('foo', 1)
        self.assertEqual(pool._pool_get('foo'), 1)
        pool._pool_del('foo')
        self.assertIsNone(pool._pool_get('foo'))

    def test_name(self):
        pool = self._makeOne()
        pool._db_flags = {'kw_args': {'db': 'foo_database'}}
        self.assertEqual(pool.name(), 'foo_database')


class PatchedDBPoolTests(PatchedConnectionTestsBase):

    def _makeOne(self, *args, **kw):
        from Products.ZMySQLDA.db import DBPool
        from Products.ZMySQLDA.db import DB
        return DBPool(DB, **kw)

    def test_variables(self):
        pool = self._makeOne()
        pool._db_flags = {'kw_args': {}}
        self.assertEqual(pool.variables(),
                         {'var1': 'val1', 'version': '5.5.5'})


class DBTests(PatchedConnectionTestsBase):

    def _makeOne(self, **kw):
        from Products.ZMySQLDA.db import DB
        return DB(**kw)

    def test_instantiation_defaults(self):
        db = self._makeOne(kw_args={})
        self.assertIsNone(db.connection)
        self.assertEqual(db._kw_args, {})
        self.assertIsNone(db._mysql_lock)
        self.assertIsNone(db._use_TM)
        self.assertIsNone(db._transactions)
        self.assertIsInstance(db.db, FakeConnection)

    def test_instantiation(self):
        db = self._makeOne(connection='conn', kw_args={'a': 1}, use_TM=True,
                           mysql_lock=True, transactions=True)
        self.assertEqual(db.connection, 'conn')
        self.assertEqual(db._kw_args, {'a': 1})
        self.assertTrue(db._mysql_lock)
        self.assertTrue(db._use_TM)
        self.assertTrue(db._transactions)

    def test_close(self):
        db = self._makeOne(kw_args={})
        db.close()
        self.assertIsNone(db.db)

    def test__parse_connection_string_empty(self):
        db = self._makeOne(kw_args={})

        parsed = db._parse_connection_string('')
        self.assertEqual(parsed['connection'], '')
        self.assertFalse(parsed['use_TM'])
        self.assertFalse('try_transactions' in parsed)
        self.assertFalse('mysql_lock' in parsed)
        self.assertFalse('db' in parsed['kw_args'])
        self.assertFalse('host' in parsed['kw_args'])
        self.assertFalse('port' in parsed['kw_args'])
        self.assertFalse('user' in parsed['kw_args'])
        self.assertFalse('passwd' in parsed['kw_args'])
        self.assertFalse('unix_socket' in parsed['kw_args'])

    def test__parse_connection_string_simple(self):
        db = self._makeOne(kw_args={})

        c_str = 'foo_db foo_user foo_pw'
        parsed = db._parse_connection_string(c_str)
        self.assertEqual(parsed['connection'], c_str)
        self.assertFalse(parsed['use_TM'])
        self.assertFalse(parsed['try_transactions'])
        self.assertFalse(parsed['mysql_lock'])
        self.assertEqual(parsed['kw_args']['db'], 'foo_db')
        self.assertFalse('host' in parsed['kw_args'])
        self.assertFalse('port' in parsed['kw_args'])
        self.assertEqual(parsed['kw_args']['user'], 'foo_user')
        self.assertEqual(parsed['kw_args']['passwd'], 'foo_pw')
        self.assertFalse('unix_socket' in parsed['kw_args'])

    def test__parse_connection_string_explicit_host(self):
        db = self._makeOne(kw_args={})

        c_str = 'foo_db@127.0.0.1:3306 foo_user foo_pw'
        parsed = db._parse_connection_string(c_str)
        self.assertEqual(parsed['connection'], c_str)
        self.assertFalse(parsed['use_TM'])
        self.assertFalse(parsed['try_transactions'])
        self.assertFalse(parsed['mysql_lock'])
        self.assertEqual(parsed['kw_args']['db'], 'foo_db')
        self.assertEqual(parsed['kw_args']['host'], '127.0.0.1')
        self.assertEqual(parsed['kw_args']['port'], 3306)
        self.assertEqual(parsed['kw_args']['user'], 'foo_user')
        self.assertEqual(parsed['kw_args']['passwd'], 'foo_pw')
        self.assertFalse('unix_socket' in parsed['kw_args'])

    def test__parse_connection_string_unix_socket(self):
        db = self._makeOne(kw_args={})

        c_str = 'foo_db foo_user foo_pw /tmp/mysql.sock'
        parsed = db._parse_connection_string(c_str)
        self.assertEqual(parsed['connection'], c_str)
        self.assertFalse(parsed['use_TM'])
        self.assertFalse(parsed['try_transactions'])
        self.assertFalse(parsed['mysql_lock'])
        self.assertEqual(parsed['kw_args']['db'], 'foo_db')
        self.assertFalse('host' in parsed['kw_args'])
        self.assertFalse('port' in parsed['kw_args'])
        self.assertEqual(parsed['kw_args']['user'], 'foo_user')
        self.assertEqual(parsed['kw_args']['passwd'], 'foo_pw')
        self.assertEqual(parsed['kw_args']['unix_socket'], '/tmp/mysql.sock')

    def test__parse_connection_string_mysql_lock(self):
        db = self._makeOne(kw_args={})

        c_str = '*mylock foo_db@127.0.0.1:3306 foo_user foo_pw'
        parsed = db._parse_connection_string(c_str)
        self.assertEqual(parsed['connection'], c_str)
        self.assertTrue(parsed['use_TM'])
        self.assertFalse(parsed['try_transactions'])
        self.assertEqual(parsed['mysql_lock'], 'mylock')
        self.assertEqual(parsed['kw_args']['db'], 'foo_db')
        self.assertEqual(parsed['kw_args']['host'], '127.0.0.1')
        self.assertEqual(parsed['kw_args']['port'], 3306)
        self.assertEqual(parsed['kw_args']['user'], 'foo_user')
        self.assertEqual(parsed['kw_args']['passwd'], 'foo_pw')
        self.assertFalse('unix_socket' in parsed['kw_args'])

    def test__parse_connection_string_transactions(self):
        db = self._makeOne(kw_args={})

        c_str = '+foo_db@127.0.0.1:3306 foo_user foo_pw'
        parsed = db._parse_connection_string(c_str)
        self.assertEqual(parsed['connection'], c_str)
        self.assertFalse(parsed['use_TM'])
        self.assertEqual(parsed['try_transactions'], '+')
        self.assertFalse(parsed['mysql_lock'])
        self.assertEqual(parsed['kw_args']['db'], 'foo_db')
        self.assertEqual(parsed['kw_args']['host'], '127.0.0.1')
        self.assertEqual(parsed['kw_args']['port'], 3306)
        self.assertEqual(parsed['kw_args']['user'], 'foo_user')
        self.assertEqual(parsed['kw_args']['passwd'], 'foo_pw')
        self.assertFalse('unix_socket' in parsed['kw_args'])

    def test_variables(self):
        db = self._makeOne(kw_args={})
        self.assertDictEqual(db.variables(),
                             {'var1': 'val1', 'version': '5.5.5'})

    def test__register(self):
        db = self._makeOne(kw_args={})
        self.assertFalse(db._registered)
        self.assertFalse(db._finalize)
        self.assertFalse(getattr(db, '_transaction_begun', False))

        db._register()
        self.assertTrue(db._registered)
        self.assertFalse(db._finalize)
        self.assertTrue(getattr(db, '_transaction_begun', False))

    def test__begin(self):
        db = self._makeOne(kw_args={})
        db._begin()
        self.assertTrue(db._transaction_begun)
        self.assertIsNone(db.db.last_query)

    def test__begin_transactions(self):
        db = self._makeOne(kw_args={})
        db._transactions = True
        db._begin()
        self.assertTrue(db._transaction_begun)
        self.assertEqual(db.db.last_query, 'BEGIN')

    def test__begin_mysql_lock(self):
        db = self._makeOne(kw_args={})
        db._mysql_lock = 'foo_lock'
        db._begin()
        self.assertTrue(db._transaction_begun)
        self.assertEqual(db.db.last_query, "SELECT GET_LOCK('foo_lock',0)")

    def test__finish(self):
        db = self._makeOne(kw_args={})

        # Without a running transaction, _abort does nothing.
        db._transaction_begun = False
        self.assertIsNone(db._finish())

        db._begin()
        db._finish()
        self.assertFalse(db._transaction_begun)
        self.assertIsNone(db.db.last_query)

    def test__finish_transactions(self):
        db = self._makeOne(kw_args={})
        db._transactions = True
        db._begin()
        db._finish()
        self.assertFalse(db._transaction_begun)
        self.assertEqual(db.db.last_query, 'COMMIT')

    def test__finish_mysql_lock(self):
        db = self._makeOne(kw_args={})
        db._mysql_lock = 'foo_lock'
        db._begin()
        db._finish()
        self.assertFalse(db._transaction_begun)
        self.assertEqual(db.db.last_query, "SELECT RELEASE_LOCK('foo_lock')")

    def test__abort(self):
        db = self._makeOne(kw_args={})

        # Without a running transaction, _abort does nothing.
        db._transaction_begun = False
        self.assertIsNone(db._abort())

        db._begin()
        db._abort()
        self.assertFalse(db._transaction_begun)
        self.assertIsNone(db.db.last_query)

    def test__abort_transactions(self):
        db = self._makeOne(kw_args={})
        db._transactions = True
        db._begin()
        db._abort()
        self.assertFalse(db._transaction_begun)
        self.assertEqual(db.db.last_query, 'ROLLBACK')

    def test__abort_mysql_lock(self):
        db = self._makeOne(kw_args={})
        db._mysql_lock = 'foo_lock'
        db._begin()
        db._abort()
        self.assertFalse(db._transaction_begun)
        self.assertEqual(db.db.last_query, "SELECT RELEASE_LOCK('foo_lock')")

    def test_savepoint(self):
        db = self._makeOne(kw_args={})

        # Really old MySQL versions don't support savepoints
        db._version = '5.0.1'
        self.assertRaises(AttributeError, db.savepoint)
        del db._version

        # If a savepoint is used outside of a transaction: AttributeError
        self.assertRaises(AttributeError, db.savepoint)

        db._begin()
        sp = db.savepoint()
        self.assertEqual(db.db.last_query, 'SAVEPOINT %s' % sp.ident)


class _SavePointTests(unittest.TestCase):

    def _makeOne(self):
        from Products.ZMySQLDA.db import _SavePoint
        return _SavePoint(FakeConnection())

    def test_initialization(self):
        sp = self._makeOne()
        self.assertIsInstance(sp.db_conn, FakeConnection)
        self.assertEqual(sp.db_conn.last_query, 'SAVEPOINT %s' % sp.ident)

    def test_rollback(self):
        sp = self._makeOne()
        sp.rollback()
        self.assertEqual(sp.db_conn.last_query, 'ROLLBACK TO %s' % sp.ident)


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(DbFunctionsTests),
                               unittest.makeSuite(DBPoolTests),
                               unittest.makeSuite(PatchedDBPoolTests),
                               unittest.makeSuite(DBTests),
                               unittest.makeSuite(_SavePointTests)))
