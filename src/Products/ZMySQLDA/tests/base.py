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
""" Base classes for unit tests
"""
import unittest
import uuid

import MySQLdb

from .dummy import FakeConnection


DB = 'zmysqldatest'
DB_USER = 'zmysqldatest'
DB_PASSWORD = 'zmysqldatest'
DB_CONN_STRING = f'{DB} {DB_USER} {DB_PASSWORD}'

random_value = uuid.uuid4().hex
TABLE_NAME = 'test_zmysqlda_%s' % str(random_value)
TABLE_COL_INT = 'c_int'
TABLE_COL_VARCHAR = 'c_varchar'

COL_INT = 'INT(10) UNSIGNED ZEROFILL NOT NULL DEFAULT 0 PRIMARY KEY'
COL_VARCHAR = 'VARCHAR(20)'

NO_MYSQL_MSG = 'Please see the documentation for running functional tests.'


def fake_connect(**kw):
    return FakeConnection(**kw)


def real_connect():
    return MySQLdb.connect(host='127.0.0.1', port=3306, user=DB_USER,
                           passwd=DB_PASSWORD, db=DB)


def have_test_database():
    """ Helper method for unittest skipping
    """
    try:
        connection = real_connect()
        connection.close()
        return True
    except MySQLdb.OperationalError as exc:  # noqa
        # print('Cannot connect to %s as %s: %s' % (DB, DB_USER, exc.args))
        return False


class PatchedConnectionTestsBase(unittest.TestCase):
    """ Tests that require faking out MySQLdb.connect
    """

    def setUp(self):
        super().setUp()

        from Products.ZMySQLDA.db import MySQLdb
        self.old_connect = MySQLdb.connect
        MySQLdb.connect = fake_connect

    def tearDown(self):
        super().tearDown()

        if getattr(self, 'conn', None):
            self.conn._v_database_connection = None
            self.conn._v_connected = None

        from Products.ZMySQLDA.db import MySQLdb
        MySQLdb.connect = self.old_connect
        from Products.ZMySQLDA.DA import database_connection_pool
        database_connection_pool.clear()


class MySQLRequiredLayer:

    @classmethod
    def setUp(cls):
        # Called only once for all tests in this layer
        # Connect to the database and (re-)create a test table,
        # but only if the test database is available to prevent tracebacks.
        # Tests classes using this layer should be skipped if the test
        # database is unavailable: "@unittest.skipUnless(have_test_database())"
        if have_test_database():
            dbconn = real_connect()
            dbconn.query('DROP TABLE IF EXISTS %s' % TABLE_NAME)
            sql = 'CREATE TABLE %s (%s %s, %s %s) ENGINE MEMORY'
            dbconn.query(sql % (TABLE_NAME, TABLE_COL_INT, COL_INT,
                                TABLE_COL_VARCHAR, COL_VARCHAR))
            dbconn.close()

    @classmethod
    def testSetUp(cls):
        from Products.ZMySQLDA import DA

        # Clean out the test table before every test
        if have_test_database():
            dbconn = real_connect()
            dbconn.query('DELETE FROM %s' % TABLE_NAME)
            dbconn.close()

        # Clear the connections cache
        DA.database_connection_pool.clear()
