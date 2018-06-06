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

from .dummy import FakeConnection


def fake_connect(**kw):
    return FakeConnection(**kw)


class PatchedConnectionTestsBase(unittest.TestCase):
    """ Tests that require faking out MySQLdb.connect
    """

    def setUp(self):
        super(PatchedConnectionTestsBase, self).setUp()

        from Products.ZMySQLDA.db import MySQLdb
        self.old_connect = MySQLdb.connect
        MySQLdb.connect = fake_connect

    def tearDown(self):
        super(PatchedConnectionTestsBase, self).tearDown()

        if getattr(self, 'conn', None):
            self.conn._v_database_connection = None
            self.conn._v_connected = None

        from Products.ZMySQLDA.db import MySQLdb
        MySQLdb.connect = self.old_connect
        from Products.ZMySQLDA.DA import database_connection_pool
        database_connection_pool.clear()
